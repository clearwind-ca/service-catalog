from django.urls import path

from . import views

app_name = "services"  # pylint: disable=invalid-name

urlpatterns = [
    path("services/", views.service_list, name="service_list"),
    path("services/<str:slug>", views.service_detail, name="service_detail"),
    path("services/<str:slug>/delete", views.service_delete, name="service_delete"),
    path("services/schema/", views.schema_detail, name="schema_detail"),
    path("sources/", views.source_list, name="source_list"),
    path("sources/add", views.source_add, name="source_add"),
    path("sources/<str:slug>/validate", views.source_validate, name="source_validate"),
    path("sources/<str:slug>/refresh", views.source_refresh, name="source_refresh"),
    path("sources/<str:slug>/delete", views.source_delete, name="source_delete"),
]
