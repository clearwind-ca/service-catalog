from django.urls import path

from . import webhooks

app_name = "github"  # pylint: disable=invalid-name


urlpatterns = [
    path("webhooks/", webhooks.webhooks, name="webhooks"),
]
