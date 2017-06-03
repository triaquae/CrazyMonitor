

from django.conf.urls import url

from  monitor import views

urlpatterns = [

    #url(r'^$',views.dashboard ),
    #url(r'^dashboard/$',views.dashboard ,name='dashboard' ),
    url(r'^triggers/$',views.triggers,name='triggers' ),
    url(r'hosts/$',views.hosts ,name='hosts'),
    url(r'host_groups/$',views.host_groups ,name='host_groups'),
    url(r'hosts/(\d+)/$',views.host_detail ,name='host_detail'),
    #url(r'graph/$',views.graph ,name='get_graph'),
    url(r'trigger_list/$',views.trigger_list ,name='trigger_list'),
    #url(r'client/service/report/$',views.service_data_report )

]
