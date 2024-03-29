from django.urls import path

from . import views

app_name = "web"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.home, name="home"),
    path("api/", views.api, name="api"),
    path("api/create/", views.api_create, name="api-create"),
    path("api/delete/", views.api_delete, name="api-delete"),
    path("setup/", views.setup, name="setup"),
    path("setup/orgs/", views.setup_orgs, name="setup-orgs"),
    path("logout/", views.logout, name="logout"),
    path("login/", views.login_problem, name="login-problem"),
]

handler403 = "web.views.handler403"
handler404 = "web.views.handler404"
handler500 = "web.views.handler500"
