from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

from .user import login_as_app


class GitHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gh"


def get_details():
    """Get permissions and events for the app."""
    try:
        gh = login_as_app()
    except ImproperlyConfigured:
        return {}

    installations = {}
    for installation in gh.get_installations():
        installations[installation.id] = {
            "permissions": installation.raw_data["permissions"],
            "events": installation.raw_data["events"],
            "html_url": installation.raw_data["html_url"],
        }
    return installations
