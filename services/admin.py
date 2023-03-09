from django.contrib import admin

from .models import Service, Source


class ServiceAdmin(admin.ModelAdmin):
    pass


class SourceAdmin(admin.ModelAdmin):
    pass


admin.site.register(Service, ServiceAdmin)
admin.site.register(Source, SourceAdmin)
