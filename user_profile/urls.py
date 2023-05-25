from django.urls import path

from . import views 

app_name="profile"

urlpatterns = [
    path("", views.profile_detail, name="profile-detail"),
    path("update/", views.profile_update, name="profile-update"),
]