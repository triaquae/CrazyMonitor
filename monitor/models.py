from django.db import models
from monitor import auth
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

# Create your models here.




class Host(models.Model):
    name =  models.CharField(max_length=64,unique=True)
    ip_addr =  models.GenericIPAddressField(unique=True)
    host_groups = models.ManyToManyField('HostGroup',blank=True) # A B C
    templates = models.ManyToManyField("Template",blank=True) # A D E
    monitored_by_choices = (
        ('agent','Agent'),
        ('snmp','SNMP'),
        ('wget','WGET'),
    )
    monitored_by = models.CharField(u'监控方式',max_length=64,choices=monitored_by_choices)
    status_choices= (
        (1,'Online'),
        (2,'Down'),
        (3,'Unreachable'),
        (4,'Offline'),
        (5,'Problem'),
    )
    host_alive_check_interval = models.IntegerField(u"主机存活状态检测间隔", default=30)
    status = models.IntegerField(u'状态',choices=status_choices,default=1)
    memo = models.TextField(u"备注",blank=True,null=True)

    def __str__(self):
        return self.name

class HostGroup(models.Model):
    name = models.CharField(max_length=64,unique=True)
    templates = models.ManyToManyField("Template",blank=True)
    memo = models.TextField(u"备注",blank=True,null=True)

    def __str__(self):
        return self.name

class ServiceIndex(models.Model):
    name = models.CharField(max_length=64)
    key =models.CharField(max_length=64)
    data_type_choices = (
        ('int',"int"),
        ('float',"float"),
        ('str',"string")
    )
    data_type = models.CharField(u'指标数据类型',max_length=32,choices=data_type_choices,default='int')
    memo = models.CharField(u"备注",max_length=128,blank=True,null=True)

    def __str__(self):
        return "%s.%s" %(self.name,self.key)

class Service(models.Model):
    name = models.CharField(u'服务名称',max_length=64,unique=True)
    interval = models.IntegerField(u'监控间隔',default=60)
    plugin_name = models.CharField(u'插件名',max_length=64,default='n/a')
    items = models.ManyToManyField('ServiceIndex',verbose_name=u"指标列表",blank=True)
    has_sub_service = models.BooleanField(default=False,help_text=u"如果一个服务还有独立的子服务 ,选择这个,比如 网卡服务有多个独立的子网卡") #如果一个服务还有独立的子服务 ,选择这个,比如 网卡服务有多个独立的子网卡
    memo = models.CharField(u"备注",max_length=128,blank=True,null=True)

    def __str__(self):
        return self.name


class Template(models.Model):
    name = models.CharField(u'模版名称',max_length=64,unique=True)
    services = models.ManyToManyField('Service',verbose_name=u"服务列表")
    triggers = models.ManyToManyField('Trigger',verbose_name=u"触发器列表",blank=True)

    def __str__(self):
        return self.name


class TriggerExpression(models.Model):
    trigger = models.ForeignKey('Trigger',verbose_name=u"所属触发器")
    service = models.ForeignKey(Service,verbose_name=u"关联服务")
    service_index = models.ForeignKey(ServiceIndex,verbose_name=u"关联服务指标")
    specified_index_key = models.CharField(verbose_name=u"只监控专门指定的指标key",max_length=64,blank=True,null=True)
    operator_type_choices = (('eq','='),('lt','<'),('gt','>'))
    operator_type = models.CharField(u"运算符",choices=operator_type_choices,max_length=32)
    data_calc_type_choices = (
        ('avg','Average'),
        ('max','Max'),
        ('hit','Hit'),
        ('last','Last'),
    )
    data_calc_func= models.CharField(u"数据处理方式",choices=data_calc_type_choices,max_length=64)
    data_calc_args = models.CharField(u"函数传入参数",help_text=u"若是多个参数,则用,号分开,第一个值是时间",max_length=64)
    threshold = models.IntegerField(u"阈值")
    logic_type_choices = (('or','OR'),('and','AND'))
    logic_type = models.CharField(u"与一个条件的逻辑关系",choices=logic_type_choices,max_length=32,blank=True,null=True)

    def __str__(self):
        return "%s %s(%s(%s))" %(self.service_index,self.operator_type,self.data_calc_func,self.data_calc_args)


class Trigger(models.Model):
    name = models.CharField(u'触发器名称',max_length=64)
    severity_choices = (
        (1,'Information'),
        (2,'Warning'),
        (3,'Average'),
        (4,'High'),
        (5,'Diaster'),
    )
    #expressions = models.ManyToManyField(TriggerExpression,verbose_name=u"条件表达式")
    severity = models.IntegerField(u'告警级别',choices=severity_choices)
    enabled = models.BooleanField(default=True)
    memo = models.TextField(u"备注",blank=True,null=True)

    def __str__(self):
        return "<serice:%s, severity:%s>" %(self.name,self.get_severity_display())


class Action(models.Model):
    """定义trigger发生后，如何报警"""
    name = models.CharField(max_length=64,unique=True)
    host_groups = models.ManyToManyField('HostGroup',blank=True) #在template里已经关联了主机和tirgger了，为什么这里还要有
    hosts = models.ManyToManyField('Host',blank=True)
    triggers = models.ManyToManyField('Trigger',blank=True,help_text=u"想让哪些trigger触发当前报警动作")
    interval = models.IntegerField(u'告警间隔(s)',default=300)
    operations = models.ManyToManyField('ActionOperation')
    recover_notice = models.BooleanField(u'故障恢复后发送通知消息',default=True)
    recover_subject = models.CharField(max_length=128,blank=True,null=True)
    recover_message = models.TextField(blank=True,null=True)

    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ActionOperation(models.Model):
    """报警动作列表"""
    name = models.CharField(max_length=64)
    step = models.SmallIntegerField(u"第n次告警",default=1,help_text="当trigger触发次数小于这个值时就执行这条记录里报警方式")
    action_type_choices = (
        ('email','Email'),
        ('sms','SMS'),
        ('script','RunScript'),
    )
    action_type = models.CharField(u"动作类型",choices=action_type_choices,default='email',max_length=64)
    notifiers= models.ManyToManyField('UserProfile',verbose_name=u"通知对象",blank=True)
    _msg_format = '''Host({hostname},{ip}) service({service_name}) has issue,msg:{msg}'''

    msg_format = models.TextField(u"消息格式",default=_msg_format)
    def __str__(self):
        return self.name


class Maintenance(models.Model):
    name =  models.CharField(max_length=64,unique=True)
    hosts = models.ManyToManyField('Host',blank=True)
    host_groups = models.ManyToManyField('HostGroup',blank=True)
    content = models.TextField(u"维护内容")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.name


class EventLog(models.Model):
    """存储报警及其它事件日志"""
    event_type_choices = ((0,'报警事件'),(1,'维护事件'))
    event_type = models.SmallIntegerField(choices=event_type_choices,default=0)
    host = models.ForeignKey("Host")
    trigger = models.ForeignKey("Trigger",blank=True,null=True)
    log = models.TextField(blank=True,null=True)
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return "host%s  %s" %(self.host , self.log)

class UserProfile(auth.AbstractBaseUser, auth.PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,

    )
    password = models.CharField(_('password'), max_length=128,
                                help_text=mark_safe('''<a class='btn-link' href='password'>重置密码</a>'''))
    phone = models.BigIntegerField(blank=True,null=True)
    weixin = models.CharField(max_length=64,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=True,
        help_text='Designates whether the user can log into this admin site.',
    )
    name = models.CharField(max_length=32)
    #role = models.ForeignKey("Role",verbose_name="权限角色")

    memo = models.TextField('备注', blank=True, null=True, default=None)
    date_joined = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['name','token','department','tel','mobile','memo']
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):  # __str__ on Python 2
        return self.email

    def has_perms(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True


    @property
    def is_superuser(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


    objects = auth.UserManager()

    class Meta:
        verbose_name = '账户'
        verbose_name_plural = '账户'






''''
CPU
    idle 80
    usage  90
    system  30
    user
    iowait  50

memory :
    usage
    free
    swap
    cache
    buffer

load:
    load1
    load 5
    load 15
'''