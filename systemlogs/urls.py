from django.urls import path

from . import views

app_name = "systemlogs"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.log_list, name="log_list"),
]
