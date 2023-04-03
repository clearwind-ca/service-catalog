from django.urls import path

from . import views

app_name = "web"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="index"),
    path("api/", views.api, name="api"),
    path("api/create", views.api_create, name="api-create"),
    path("api/delete", views.api_delete, name="api-delete"),
    path("debug/", views.debug, name="debug"),
    path("logout", views.logout, name="logout"),
]

handler404 = "web.views.handler404"
handler500 = "web.views.handler500"
