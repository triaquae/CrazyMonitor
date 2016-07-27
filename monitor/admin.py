from django.contrib import admin


import models
# Register your models here.

class HostAdmin(admin.ModelAdmin):
    list_display =  ('id','ip_addr','status')
    filter_horizontal = ('host_groups','templates')
class TemplateAdmin(admin.ModelAdmin):
    filter_horizontal = ('services','triggers')

class ServiceAdmin(admin.ModelAdmin):
    filter_horizontal = ('items',)
    list_display = ('name','interval','plugin_name')
    #list_select_related = ('items',)


class TriggerExpressionInline(admin.TabularInline):
    model = models.TriggerExpression
    #exclude = ('memo',)
    #readonly_fields = ['create_date']
class TriggerAdmin(admin.ModelAdmin):
    list_display = ('name','severity','enabled')
    inlines = [TriggerExpressionInline,]
    #filter_horizontal = ('expressions',)
class TriggerExpressionAdmin(admin.ModelAdmin):
    list_display = ('trigger','service','service_index','specified_index_key','operator_type','data_calc_func','threshold','logic_type')

#class ActionConditionAdmin(admin.ModelAdmin):
#    list_display = ('id','action','trigger','logic_type')
#    ordering = ('id',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','name','phone','weixin','email')
admin.site.register(models.Host,HostAdmin)
admin.site.register(models.HostGroup)
admin.site.register(models.Template,TemplateAdmin)
admin.site.register(models.Service,ServiceAdmin)
admin.site.register(models.Trigger,TriggerAdmin)
admin.site.register(models.TriggerExpression,TriggerExpressionAdmin)
admin.site.register(models.ServiceIndex)
admin.site.register(models.Action)
admin.site.register(models.ActionOperation)
#admin.site.register(models.ActionCondtion,ActionConditionAdmin)
admin.site.register(models.Maintenance)
admin.site.register(models.UserProfile,UserProfileAdmin)