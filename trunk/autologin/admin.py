from django.contrib import admin

from autologin.models import AutologinToken

class AutologinTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires',)

    
admin.site.register(AutologinToken, AutologinTokenAdmin)