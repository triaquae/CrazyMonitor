#_*_coding:utf-8_*_
__author__ = 'Alex Li'

from monitor.backends import redis_conn
import pickle,time
from monitor import models
from django.core.mail import send_mail
from CrazyMonitor import settings

class TriggerHandler(object):

    def __init__(self,django_settings):
        self.django_settings = django_settings
        self.redis = redis_conn.redis_conn(self.django_settings)
        self.alert_counters ={} #纪录每个action的触发报警次数
        '''alert_counters = {
            1: {2:{'counter':0,'last_alert':None}, #k 1是主机id, {2:{'counter'}} 2是trigger id
                4:{'counter':1,'last_alert':None}},  #k是action id, 
            #2: {2:0},
        }'''



    def start_watching(self):
        '''
        start listening and watching the needed to be handled triggers from other process
        :return:
        '''

        radio = self.redis.pubsub()
        radio.subscribe(self.django_settings.TRIGGER_CHAN)
        radio.parse_response() #ready to watch
        print("\033[43;1m************start listening new triggers**********\033[0m")
        self.trigger_count = 0
        while True:
            msg = radio.parse_response()
            self.trigger_consume(msg)

    def trigger_consume(self,msg):
        self.trigger_count +=1
        print("\033[41;1m************Got a trigger msg [%s]**********\033[0m" % self.trigger_count)
        trigger_msg = pickle.loads(msg[2])
        #print("msg:",pickle.loads(msg[2]))
        #print(trigger_msg)
        #print(trigger_msg['positive_expressions'][0]['expression_obj'])
        action = ActionHandler(trigger_msg,self.alert_counters)
        action.trigger_process()


class ActionHandler(object):
    '''
    负责把达到报警条件的trigger进行分析 ,并根据 action 表中的配置来进行报警
    '''

    def __init__(self,trigger_data,alert_counter_dic):
        self.trigger_data = trigger_data
        #self.trigger_process()
        self.alert_counter_dic = alert_counter_dic

    def record_log(self,action_obj,action_operation,host_id,trigger_data):
        """record alert log into DB"""
        models.EventLog.objects.create(
            event_type = 0,
            host_id=host_id,
            trigger_id = trigger_data.get('trigger_id'),
            log = trigger_data
        )


    def action_email(self,action_obj,action_operation_obj,host_id,trigger_data):
        '''
        sending alert email to who concerns.
        :param action_obj: 触发这个报警的action对象
        :param action_operation_obj: 要报警的动作对象
        :param host_id: 要报警的目标主机
        :param trigger_data: 要报警的数据
        :return:
        '''

        print("要发报警的数据:",self.alert_counter_dic[action_obj.id][host_id])
        print("action email:",action_operation_obj.action_type,action_operation_obj.notifiers,trigger_data)
        notifier_mail_list = [obj.email for obj in action_operation_obj.notifiers.all()]
        subject = '级别:%s -- 主机:%s -- 服务:%s' %(trigger_data.get('trigger_id'),
                                              trigger_data.get('host_id'),
                                              trigger_data.get('service_item'))

        send_mail(
            subject,
            action_operation_obj.msg_format,
            settings.DEFAULT_FROM_EMAIL,
            notifier_mail_list,
        )

    def trigger_process(self):
        '''
        分析trigger并报警
        :return:
        '''
        print('Action Processing'.center(50,'-'))

        if self.trigger_data.get('trigger_id') == None: #trigger id == None
            print(self.trigger_data)
            if self.trigger_data.get('msg'):
                print(self.trigger_data.get('msg'))

                #既然没有trigger id,直接报警给管理 员
            else:
                print("\033[41;1mInvalid trigger data %s\033[0m" % self.trigger_data)

        else:#正经的trigger 报警要触发了
            print("\033[33;1m%s\033[0m" %self.trigger_data)

            trigger_id = self.trigger_data.get('trigger_id')
            host_id = self.trigger_data.get('host_id')
            trigger_obj = models.Trigger.objects.get(id=trigger_id)
            actions_set = trigger_obj.action_set.select_related() #找到这个trigger所关联的action list
            print("actions_set:",actions_set)
            matched_action_list = set() # 一个空集合
            for action in actions_set:
                #每个action 都 可以直接 包含多个主机或主机组,
                # 为什么tigger里关联了template,template里又关联了主机，那action还要直接关联主机呢？
                #那是因为一个trigger可以被多个template关联，这个trigger触发了，不一定是哪个tempalte里的主机导致的
                for hg in action.host_groups.select_related():
                    for h in hg.host_set.select_related():
                        if h.id == host_id:# 这个action适用于此主机
                            matched_action_list.add(action)
                            if action.id not in self.alert_counter_dic: #第一次被 触,先初始化一个action counter dic
                                self.alert_counter_dic[action.id] = {}
                            print("action, ",id(action))
                            if h.id not in self.alert_counter_dic[action.id]:  # 这个主机第一次触发这个action的报警
                                self.alert_counter_dic[action.id][h.id] = {'counter': 0, 'last_alert': time.time()}
                                # self.alert_counter_dic.setdefault(action,{h.id:{'counter':0,'last_alert':time.time()}})
                            else:
                                #如果达到报警触发interval次数，就记数+1
                                if time.time() - self.alert_counter_dic[action.id][h.id]['last_alert'] >= action.interval:
                                    self.alert_counter_dic[action.id][h.id]['counter'] += 1
                                    #self.alert_counter_dic[action.id][h.id]['last_alert'] = time.time()

                                else:
                                    print("没达到alert interval时间,不报警",action.interval,
                                          time.time() - self.alert_counter_dic[action.id][h.id]['last_alert'])
                            #self.alert_counter_dic.setdefault(action.id,{})

                for host in action.hosts.select_related():
                    if host.id == host_id:   # 这个action适用于此主机
                        matched_action_list.add(action)
                        if action.id not in self.alert_counter_dic:  # 第一次被 触,先初始化一个action counter dic
                            self.alert_counter_dic[action.id] = {}
                        if h.id not in self.alert_counter_dic[action.id]: #这个主机第一次触发这个action的报警
                            self.alert_counter_dic[action.id][h.id] ={'counter': 0, 'last_alert': time.time()}
                            #self.alert_counter_dic.setdefault(action,{h.id:{'counter':0,'last_alert':time.time()}})
                        else:
                            # 如果达到报警触发interval次数，就记数+1
                            if time.time() - self.alert_counter_dic[action.id][h.id]['last_alert'] >= action.interval:
                                self.alert_counter_dic[action.id][h.id]['counter'] += 1
                                #self.alert_counter_dic[action.id][h.id]['last_alert'] = time.time()
                            else:
                                print("没达到alert interval时间,不报警", action.interval,
                                      time.time() - self.alert_counter_dic[action.id][h.id]['last_alert'])


            print("alert_counter_dic:",self.alert_counter_dic)
            print("matched_action_list:",matched_action_list)
            for action_obj in matched_action_list:#
                if time.time() - self.alert_counter_dic[action_obj.id][host_id]['last_alert'] >= action_obj.interval:
                    #该报警 了
                    print("该报警了.......",time.time() - self.alert_counter_dic[action_obj.id][host_id]['last_alert'],action_obj.interval)
                    for action_operation in action_obj.operations.select_related().order_by('-step'):
                        if action_operation.step > self.alert_counter_dic[action_obj.id][host_id]['counter']:
                            #就
                            print("##################alert action:%s" %
                                  action_operation.action_type,action_operation.notifiers)

                            action_func = getattr(self,'action_%s'% action_operation.action_type)
                            action_func(action_obj,action_operation,host_id,self.trigger_data)

                            #报完警后更新一下报警时间 ，这样就又重新计算alert interval了
                            self.alert_counter_dic[action_obj.id][host_id]['last_alert'] = time.time()
                            self.record_log(action_obj,action_operation,host_id,self.trigger_data)
                        # else:
                        #     print("离下次触发报警的时间还有[%s]s" % )