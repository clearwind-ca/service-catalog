from django.contrib import admin

from .models import Service, Source, Organization


class ServiceAdmin(admin.ModelAdmin):
    pass


class SourceAdmin(admin.ModelAdmin):
    pass

class OrganizationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Service, ServiceAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Organization, OrganizationAdmin)