from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "logs"  # pylint: disable=invalid-name

router = routers.DefaultRouter()
router.register("logs", views.SystemLogViewSet, basename="api")

urlpatterns = [
    path("logs/list/", views.log_list, name="log-list"),
    path("logs/<pk>/", views.log_details, name="log-details"),
    path("api/", include(router.urls)),
]
