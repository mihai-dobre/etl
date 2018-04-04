from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
# from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter

from .models import InputFile, Agent, IP, Request, CustomUser


class InputFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'md5',
                    'path')


class UserAgentAdmin(admin.ModelAdmin):
    list_display = ('op_sys',
                    'op_sys_version',
                    'device',
                    'device_brand',
                    'device_type',
                    'browser',
                    'browser_version')


class IPAdmin(admin.ModelAdmin):
    list_display = ('ip',
                    'city',
                    'country')


class RequestAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'user',
        'ip',
        'agent',
        'file'
    )

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_id',)

admin.site.register(InputFile, InputFileAdmin)
admin.site.register(Agent, UserAgentAdmin)
admin.site.register(IP, IPAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
