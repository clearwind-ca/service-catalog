from django.conf import settings
from django.contrib.auth import get_user_model
from github import Github, enable_console_debug_logging
from oauthlogin.models import OAuthConnection


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


def check_org_membership(username, org):
    gh = login_as_user(settings.CRON_USER)
    try:
        org_object = gh.get_organization(org)
        org_object.has_in_members(username)
        return True
    except AssertionError:
        return False
