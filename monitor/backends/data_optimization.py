#_*_coding:utf-8_*_
__author__ = 'Alex Li'

from CrazyMonitor import settings
import time ,json
import copy
class DataStore(object):
    '''
    processing the client reported service data , do some data optimiaztion and save it into redis DB
    '''
    def __init__(self, client_id,service_name, data,redis_obj):
        '''

        :param client_id:
        :param service_name:
        :param data: the client reported service clean data ,
        :return:
        '''
        self.client_id = client_id
        self.service_name = service_name
        self.data = data
        self.redis_conn_obj = redis_obj
        self.process_and_save()

    def get_data_slice(self,lastest_data_key,optimization_interval):
        '''
        :param optimization_interval: e.g: 600, means get latest 10 mins real data from redis
        :return:
        '''
        all_real_data = self.redis_conn_obj.lrange(lastest_data_key,1,-1)
        #print("get data range of:",lastest_data_key,optimization_interval)
        #print("get data range of:",all_real_data[-1])
        data_set = []
        for item in all_real_data:
            #print(json.loads(item))
            data  = json.loads(item.decode())
            if len(data) ==2:
                #print("real data item:",data[0],data[1])
                service_data, last_save_time = data
                #print('time:',time.time(), time.time()- last_save_time, optimization_interval)
                if time.time() - last_save_time <= optimization_interval:# filter this data point out
                    #print(time.time()- last_save_time, optimization_interval)
                    data_set.append(data)
                else:
                    pass
        #print('data set:--->',data_set)
        return data_set
    def process_and_save(self):
        '''
        processing data and save into redis
        :return:
        '''
        print("\033[42;1m---service data-----------------------\033[0m")
        #print( self.client_id,self.service_name,self.data)
        if self.data['status'] ==0:# service data is valid
            for key,data_series_val in settings.STATUS_DATA_OPTIMIZATION.items():
                data_series_optimize_interval,max_data_point = data_series_val
                data_series_key_in_redis = "StatusData_%s_%s_%s" %(self.client_id,self.service_name,key)
                #print(data_series_key_in_redis,data_series_val)
                last_point_from_redis = self.redis_conn_obj.lrange(data_series_key_in_redis,-1,-1)
                if not last_point_from_redis: #this key is not exist in redis
                    #so initialize a new key ,the first data point in the data set will only be used to identify that when  \
                    #the data got saved last time
                    self.redis_conn_obj.rpush(data_series_key_in_redis,json.dumps([None,time.time()] ))
                if data_series_optimize_interval == 0:#this dataset is for unoptimized data, only the latest data no need optimiaztion
                    self.redis_conn_obj.rpush(data_series_key_in_redis,json.dumps([self.data, time.time()]))

                else: #data might needs to be optimized
                    #print("*****>>",self.redis_conn_obj.lrange(data_series_key_in_redis,-2,-1))
                    last_point_data,last_point_save_time =  \
                        json.loads(self.redis_conn_obj.lrange(data_series_key_in_redis,-1,-1)[0].decode())

                    if time.time() - last_point_save_time >= data_series_optimize_interval: # reached the data point update interval ,
                        lastest_data_key_in_redis = "StatusData_%s_%s_latest" %(self.client_id,self.service_name)
                        print("calulating data for key:\033[31;1m%s\033[0m" %data_series_key_in_redis )
                        #最近n分钟的数据 已经取到了,放到了data_set里

                        data_set = self.get_data_slice(lastest_data_key_in_redis,data_series_optimize_interval)
                        print('--------------------------len dataset :',len(data_set))
                        if len(data_set)>0:
                            #接下来拿这个data_set交给下面这个方法,让它算出优化的结果 来
                            optimized_data = self.get_optimized_data(data_series_key_in_redis, data_set)
                            if optimized_data:
                                self.save_optimized_data(data_series_key_in_redis, optimized_data)
                #同时确保数据在redis中的存储数量不超过settings中指定 的值
                if self.redis_conn_obj.llen(data_series_key_in_redis) >= max_data_point:
                    self.redis_conn_obj.lpop(data_series_key_in_redis) #删除最旧的一个数据
                #self.redis_conn_obj.ltrim(data_series_key_in_redis,0,data_series_val[1])
        else:
            print("report data is invalid::",self.data)
            raise ValueError

    def save_optimized_data(self,data_series_key_in_redis, optimized_data):
        '''
        save the optimized data into db
        :param optimized_data:
        :return:
        '''
        self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([optimized_data, time.time()])   )

    def get_optimized_data(self,data_set_key, raw_service_data):
        '''
        calculate out ava,max,min,mid value from raw service data set
        :param data_set_key: where the optimized data needed to save to in redis db
        :param raw_service_data: raw service data data list
        :return:
        '''
        #index_init =[avg,max,min,mid]
        print("get_optimized_data:",raw_service_data[0] )
        service_data_keys = raw_service_data[0][0].keys() #[iowait, idle,system...]
        first_service_data_point = raw_service_data[0][0] # use this to build up a new empty dic
        #print("--->",service_data_keys)
        optimized_dic = {} #set a empty dic, will save optimized data later
        if 'data' not  in service_data_keys: #means this dic has  no subdic, works for service like cpu,memory
            for key in service_data_keys:
                optimized_dic[key] = []
            #optimized_dic = optimized_dic.fromkeys(first_service_data_point,[])
            tmp_data_dic = copy.deepcopy(optimized_dic)  #为了临时存最近n分钟的数据 ,把它们按照每个指标 都 搞成一个一个列表 ,来存最近N分钟的数据
            print("tmp data dic:",tmp_data_dic)
            for service_data_item,last_save_time in raw_service_data: #loop 最近n分钟的数据
                #print(service_data_item)
                for service_index,v in service_data_item.items(): #loop 每个数据点的指标
                    #print(service_index,v)
                    try:
                        tmp_data_dic[service_index].append(round(float(v),2)) #把这个点的当前这个指标 的值 添加到临时dict中
                    except ValueError as e:
                        pass
                #print(service_data_item,last_save_time)
            for service_k,v_list in tmp_data_dic.items():
                print(service_k, v_list)
                avg_res = self.get_average(v_list)
                max_res = self.get_max(v_list)
                min_res = self.get_min(v_list)
                mid_res = self.get_mid(v_list)
                optimized_dic[service_k]= [avg_res,max_res,min_res,mid_res]
                print(service_k, optimized_dic[service_k])

        else: # has sub dic inside key 'data', works for a service has multiple independent items, like many ethernet,disks...
            #print("**************>>>",first_service_data_point )
            for service_item_key,v_dic in first_service_data_point['data'].items():
                #service_item_key 相当于lo,eth0,... , v_dic ={ t_in:333,t_out:3353}
                optimized_dic[service_item_key] = {}
                for k2,v2 in v_dic.items():
                    optimized_dic[service_item_key][k2] = [] #{etho0:{t_in:[],t_out:[]}}

            tmp_data_dic = copy.deepcopy(optimized_dic)
            if tmp_data_dic: #some times this tmp_data_dic might be empty due to client report err
                print('tmp data dic:', tmp_data_dic)
                for service_data_item,last_save_time in raw_service_data:#loop最近n分钟数据
                    for service_index,val_dic in service_data_item['data'].items():
                        #print(service_index,val_dic)
                        #service_index这个值 相当于eth0,eth1...
                        for service_item_sub_key, val in val_dic.items():
                            #上面这个service_item_sub_key相当于t_in,t_out
                            #if service_index == 'lo':
                            #print(service_index,service_item_sub_key,val)
                            tmp_data_dic[service_index][service_item_sub_key].append(round(float(val),2))
                            #上面的service_index变量相当于 eth0...
                for service_k,v_dic in tmp_data_dic.items():
                    for service_sub_k,v_list in v_dic.items():
                        print(service_k, service_sub_k, v_list)
                        avg_res = self.get_average(v_list)
                        max_res = self.get_max(v_list)
                        min_res = self.get_min(v_list)
                        mid_res = self.get_mid(v_list)
                        optimized_dic[service_k][service_sub_k] = [avg_res,max_res,min_res,mid_res]
                        print(service_k, service_sub_k, optimized_dic[service_k][service_sub_k])

            else:
                print("\033[41;1mMust be sth wrong with client report data\033[0m")
        print("optimized empty dic:", optimized_dic)

        return optimized_dic


    def get_average(self,data_set):
        '''
        calc the avg value of data set
        :param data_set:
        :return:
        '''
        if len(data_set) >0:
            return sum(data_set) /len(data_set)
        else:
            return 0
    def get_max(self,data_set):
        '''
        calc the max value of the data set
        :param data_set:
        :return:
        '''
        if len(data_set) >0:
            return max(data_set)
        else:
            return 0
    def get_min(self,data_set):
        '''
        calc the minimum value of the data set
        :param data_set:
        :return:
        '''
        if len(data_set) >0:
            return min(data_set)
        else:
            return 0
    def get_mid(self,data_set):
        '''
        calc the mid value of the data set
        :param data_set:
        :return:
        '''
        data_set.sort()
        #[1,4,99,32,8,9,4,5,9]
        #[1,3,5,7,9,22,54,77]
        if len(data_set) >0:
            return data_set[  int(len(data_set)/2) ]
        else:
            return 0
