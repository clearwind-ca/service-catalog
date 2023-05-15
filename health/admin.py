from django.contrib import admin

from .models import CheckResult, Check


class CheckAdmin(admin.ModelAdmin):
    pass


class CheckResultAdmin(admin.ModelAdmin):
    pass


admin.site.register(Check, CheckAdmin)
admin.site.register(CheckResult, CheckResultAdmin)
