from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "health"  # pylint: disable=invalid-name

router = routers.DefaultRouter()
router.register("check", views.CheckViewSet, basename="api-check")
router.register("result", views.CheckResultViewSet, basename="api-result")

urlpatterns = [
    path("health/", views.checks, name="checks-list"),
    path("health/add/", views.checks_add, name="checks-add"),
    path("health/<str:slug>/detail/", views.checks_detail, name="checks-detail"),
    path("health/<str:slug>/update/", views.checks_update, name="checks-update"),
    path("health/<str:slug>/delete/", views.checks_delete, name="checks-delete"),
    path("health/<str:slug>/run/", views.checks_run, name="checks-run"),
    path("results/", views.results, name="results-list"),
    path("results/<pk>/detail/", views.results_detail, name="results-detail"),
    path("api/", include(router.urls)),
    path("api/health/<pk>/run/", views.api_checks_run, name="api-checks-run"),
]
