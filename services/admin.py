from django.contrib import admin

from .models import Organization, Service, Source


class ServiceAdmin(admin.ModelAdmin):
    pass


class SourceAdmin(admin.ModelAdmin):
    pass


class OrganizationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Service, ServiceAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Organization, OrganizationAdmin)
