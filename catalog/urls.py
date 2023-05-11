from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", include("web.urls")),
    path("", include("services.urls")),
    path("", include("health.urls")),
    path("", include("events.urls")),
    path("", include("systemlogs.urls")),
    path("github/", include("gh.urls")),
    path("oauth/", include("oauthlogin.urls")),
    path("admin/", admin.site.urls),
    path(
        "api-schema/",
        TemplateView.as_view(
            template_name="api-schema.yml",
        ),
        name="api-schema",
    ),
    path(
        "api-docs/",
        TemplateView.as_view(
            template_name="api-docs.html", extra_context={"schema_url": "api-schema"}
        ),
        name="api-docs-ui",
    ),
]


handler403 = "web.views.handler403"
handler404 = "web.views.handler404"
handler500 = "web.views.handler500"
