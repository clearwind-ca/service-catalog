from django.urls import path

from . import views

app_name = "deployments"  # pylint: disable=invalid-name

urlpatterns = [
    path("deployments", views.deployments, name="deployments"),
]
