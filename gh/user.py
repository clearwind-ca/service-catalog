from django.conf import settings
from github import Github, enable_console_debug_logging
from oauthlogin.models import OAuthConnection


def login_as_user(user):
    """Login as the user."""
    connection = OAuthConnection.objects.get(user=user, provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    if settings.GITHUB_DEBUG:
        enable_console_debug_logging()
    return Github(connection.access_token)
