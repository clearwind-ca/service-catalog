from django.urls import path

from . import views

app_name = "health"  # pylint: disable=invalid-name

urlpatterns = [
    path("health/", views.checks, name="checks-list"),
    path("health/add/", views.checks_add, name="checks-add"),
    path("health/detail/<str:slug>/", views.checks_detail, name="checks-detail"),
    path("results/", views.results, name="results-list"),
]
