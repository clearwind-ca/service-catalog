from django.conf import settings
from github import Github, enable_console_debug_logging
from oauthlogin.models import OAuthConnection
from django.contrib.auth import get_user_model

def login_as_user(user):
    """Login as the user."""
    if isinstance(user, str):
        user = get_user_model().objects.get(username=user)

    connection = OAuthConnection.objects.get(user=user, provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    if settings.GITHUB_DEBUG:
        enable_console_debug_logging()
    return Github(connection.access_token)
