from django.urls import path

from . import views

app_name = "services"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.list, name="list"),
    path("<str:slug>", views.show, name="show"),
]
