from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "systemlogs"  # pylint: disable=invalid-name

router = routers.DefaultRouter()
router.register("list", views.SystemLogViewSet, basename="api")

urlpatterns = [
    path("list", views.log_list, name="log_list"),
    path("api/", include(router.urls))
]
