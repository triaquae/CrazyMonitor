#_*_coding:utf-8_*_
__author__ = 'Alex Li'

from  monitor import models
import json
from CrazyMonitor import  settings

class GraphGenerator2(object):
    '''
    产生流量图
    '''
    def __init__(self,request,redis_obj):
        self.request = request
        self.redis = redis_obj
        self.host_id = self.request.GET.get('host_id')
        self.time_range = self.request.GET.get('time_range')

    def get_host_graph(self):
        '''
        生成此主机关联的所有图
        :return:
        '''
        host_obj = models.Host.objects.get(id=self.host_id)
        service_data_dic = {}
        template_list = list(host_obj.templates.select_related())
        for g in host_obj.host_groups.select_related():
            template_list.extend(list(g.templates.select_related()))
        template_list = set(template_list)
        for template in template_list:
            for service in template.services.select_related():
                service_data_dic[service.id] = {
                    'name':service.name,
                    'index_data':{},
                    'has_sub_service': service.has_sub_service,
                    'raw_data':[],
                    'items': [item.key for item in service.items.select_related() ]
                }
                '''if not service.has_sub_service:
                    for index in service.items.select_related():
                        service_data_dic[service.id]['index_data'][index.key] = {
                            'id': index.id,
                            'name':index.name,
                            'data':[]
                        }
                #else: #like nic service
                '''

        print(service_data_dic)
        #service_data_dic
        #开始取数据
        for service_id,val_dic in service_data_dic.items():
            #if val_dic['has_sub_service'] == False:
            service_redis_key = "StatusData_%s_%s_%s" %(self.host_id,val_dic['name'],self.time_range)
            print('service_redis_key',service_redis_key)
            service_raw_data = self.redis.lrange(service_redis_key,0,-1)
            service_raw_data =  [item.decode() for item in service_raw_data]
            service_data_dic[service_id]['raw_data'] = service_raw_data

        return service_data_dic

class GraphGenerator(object):
    '''
    generate graphs
    '''

    def __init__(self,request,redis_obj):
        self.request = request
        self.host_id = self.request.GET.get('host_id')
        self.service_name = self.request.GET.get('service_key')
        self.index_key = self.request.GET.get('index_key')
        self.time_range = self.request.GET.get('time_range')
        self.sub_service_name = self.request.GET.get('sub_service_key')
        self.redis = redis_obj

        print("sub service key:", self.sub_service_name)

    def get_graph_data(self):
        #data_store_key = "StatusData_%s_%s_latest" %(self.host_id,self.service_name)
        data_store_key = "StatusData_%s_%s_%s" %(self.host_id,self.service_name,self.time_range)
        data_set = self.redis.lrange(data_store_key,0,-1)
        print("data store key:", data_store_key)
        print("data point nums:", len(data_set))
        #print("data points:", data_set)
        service_obj = models.Service.objects.get(name=self.service_name)
        data_dic = {} #store graph data later
        for item in service_obj.items.select_related():
            data_dic[item.key] = []

        if data_set: #make sure data set not empty

            print("service data for graph:", data_dic)
            if self.sub_service_name == None or self.sub_service_name == 'undefined':
                for data_point in data_set:
                    #data_point sample data:('-->', {u'status': 0, u'iowait': u'0.00', u'system': u'1.01', u'idle': u'96.98', u'user': u'2.01', u'steal': u'0.00', u'nice': u'0.00'}, 1461840915.038072)
                    val,timestamp = json.loads(data_point)
                    if val:
                        for k,v in val.items():
                            if k in data_dic:
                                '''if len(data_dic[k]) > 0: #不是第一次存值
                                    last_point_save_time = data_dic[k][-1][0] #microseconds
                                    data_point_interval =settings.STATUS_DATA_OPTIMIZATION[self.time_range][0]
                                    if timestamp*1000 - last_point_save_time > data_point_interval:
                                        #这里出现中断了
                                        data_dic[k].append([last_point_save_time + data_point_interval,0])
                                    else:#没有中断过,什么都 不用做哈哈
                                        pass
                                '''
                                if type(v) is not list:
                                    data_dic[k].append([timestamp*1000,float(v)])
                                else: #v = [avg,max,min,mid]
                                    data_dic[k].append([timestamp*1000,float(v[0])]) #暂时只往前台 返回 average数据
            else: #has sub service
               print("\033[44;1m------------subservice key: %s, %s\033[0m" %(self.sub_service_name,self.service_name))
               for data_point in data_set:
                    #data_point sample data:('-->', {u'status': 0, u'iowait': u'0.00', u'system': u'1.01', u'idle': u'96.98', u'user': u'2.01', u'steal': u'0.00', u'nice': u'0.00'}, 1461840915.038072)
                    val,timestamp = json.loads(data_point)
                    if val:
                        if val.get('data'):
                            for sub_service_key,v_dic in val['data'].items():
                                for k,v in v_dic.items():
                                    if k  in data_dic:
                                        if type(v) is not list:
                                            data_dic[k].append([timestamp*1000,float(v)])
                                        else: #v = [avg,max,min,mid]
                                            data_dic[k].append([timestamp*1000,float(v[0])]) #暂时只往前台 返回 average数据

        for k,v in data_dic.items():
            print(k,v)

        return data_dic