#_*_coding:utf-8_*_
__author__ = 'Alex Li'

from monitor.backends import redis_conn
import pickle,time
from monitor import models
class TriggerHandler(object):

    def __init__(self,django_settings):
        self.django_settings = django_settings
        self.redis = redis_conn.redis_conn(self.django_settings)
        self.alert_counters ={} #纪录每个action的触发报警次数
        alert_counters = {
            1: {2:{'counter':0,'last_alert':None},
                4:{'counter':1,'last_alert':None}},  #k是action id, {2:0,3:2}这里面的k是主机id,value是报警次数
            #2: {2:0},
        }



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
    负责把达到报警条件 的trigger进行分析 ,并根据 action 表中的配置来进行报警
    '''

    def __init__(self,trigger_data,alert_counter_dic):
        self.trigger_data = trigger_data
        #self.trigger_process()
        self.alert_counter_dic = alert_counter_dic
    def trigger_process(self):
        '''
        分析trigger并报警
        :return:
        '''
        print('Action Processing'.center(50,'-'))
        print(self.trigger_data)
        if self.trigger_data.get('trigger_id') == None: #trigger id == None
            if self.trigger_data.get('msg'):
                print(self.trigger_data.get('msg'))

                #既然没有trigger id,直接报警给管理 员
            else:
                print("\033[41;1mInvalid trigger data %s\033[0m" % self.trigger_data)
        else:#正经的trigger 报警要触发了
            trigger_id = self.trigger_data.get('trigger_id')
            host_id = self.trigger_data.get('host_id')
            trigger_obj = models.Trigger.objects.get(id=trigger_id)
            actions_set = trigger_obj.action_set.select_related() #找到这个trigger所关联的action list
            matched_action_list = {} # 一个空集合
            for action in actions_set:
                #每个action 都 可以直接 包含多个主机或主机组,
                for hg in action.host_groups.select_related():
                    for h in hg.host_set.select_related():
                        if h.id == host_id:# 这个action适用于此主机
                            matched_action_list.add(action)
                            if action.id not in self.alert_counter_dic: #第一次被 触,先初始化一个action counter dic
                                self.alert_counter_dic[action] = {h.id:{'counter':0,'last_alert':time.time()}}
                            #self.alert_counter_dic.setdefault(action.id,{})

                for host in action.hosts.select_related():
                    if host.id == host_id:   # 这个action适用于此主机
                        matched_action_list.add(action)
                        self.alert_counter_dic.setdefault(action,{h.id:{'counter':0,'last_alert':time.time()}})

            for action_obj in matched_action_list:#
                if time.time() - self.alert_counter_dic[action_obj][host_id]['last_alert'] >= action_obj.interval:
                    #该报警 了
                    for action_operation in action_obj.operations.select_related().order('-step'):
                        if action_operation.step > self.alert_counter_dic[action_obj][host_id]['counter']:
                            #就
                            print("alert action:%s" % action.action_type,action.notifiers)