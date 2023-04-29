from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "services"  # pylint: disable=invalid-name

router = routers.DefaultRouter()
router.register("source", views.SourceViewSet, basename="api-source")
router.register("service", views.ServiceViewSet, basename="api-service")

urlpatterns = [
    path("services/", views.service_list, name="service-list"),
    path("services/<str:slug>/", views.service_detail, name="service-detail"),
    path("services/<str:slug>/delete/", views.service_delete, name="service-delete"),
    path("schema/", views.schema_detail, name="schema-detail"),
    path("sources/", views.source_list, name="source-list"),
    path("sources/add/", views.source_add, name="source-add"),
    path("org/add/", views.org_add, name="org-add"),
    path("sources/<str:slug>/", views.source_detail, name="source-detail"),
    path("sources/<str:slug>/validate/", views.source_validate, name="source-validate"),
    path("sources/<str:slug>/refresh/", views.source_refresh, name="source-refresh"),
    path("sources/<str:slug>/delete/", views.source_delete, name="source-delete"),
    path("sources/<str:slug>/update/", views.source_update, name="source-update"),
    path("api/", include(router.urls)),
    path("api/sources/<pk>/refresh/", views.api_source_refresh, name="api-source-refresh"),
    path("api/sources/<pk>/validate/", views.api_source_validate, name="api-source-validate"),
    path("api/services/schema/", views.api_schema_detail, name="api-schema-detail"),
]
