from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "events"  # pylint: disable=invalid-name

router = routers.DefaultRouter()
router.register("events", views.EventViewSet, basename="api-events")

urlpatterns = [
    path("events/", views.events_list, name="events-list"),
    path("events/add/", views.events_add, name="events-add"),
    path("events/<str:pk>/update/", views.events_update, name="events-update"),
    path("events/<str:pk>/details/", views.events_detail, name="events-detail"),
    path("events/<str:pk>/delete/", views.events_delete, name="events-delete"),
    path("api/", include(router.urls)),
]
