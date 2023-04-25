from django.urls import path

from . import views

app_name = "events"  # pylint: disable=invalid-name

urlpatterns = [
    path("events", views.events_list, name="events-list"),
    path("events/add/", views.events_add, name="events-add"),
    path("events/<str:slug>/update/", views.events_update, name="events-update"),
    path("events/<str:slug>/details/", views.events_details, name="events-details"),
]
