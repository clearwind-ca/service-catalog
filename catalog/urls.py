from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("web.urls")),
    path("", include("services.urls")),
    path("oauth/", include("oauthlogin.urls")),
    path("admin/", admin.site.urls),
]
