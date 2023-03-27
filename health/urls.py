from django.urls import path

from . import views

app_name = "health"  # pylint: disable=invalid-name

urlpatterns = [
    path("health", views.health, name="health"),
]
