from django.urls import path

from . import views

app_name = "services"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.service_list, name="service_list"),
    path("<str:slug>", views.service_detail, name="service_detail"),
    path("<str:slug>/delete", views.service_delete, name="service_delete"),
    path("sources/", views.source_list, name="source_list"),
    path("sources/<str:slug>/refresh", views.source_refresh, name="source_refresh"),
]
