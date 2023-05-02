import os

from django.conf import settings
from django.contrib.auth import get_user_model
from github import Github, GithubIntegration, enable_console_debug_logging
from oauthlogin.models import OAuthConnection

if settings.GITHUB_DEBUG:
    enable_console_debug_logging()


def login_as_app():
    """Login as the app."""
    return GithubIntegration(os.environ.get("GITHUB_APP_ID"), os.environ.get("GITHUB_PEM"))


def login_as_user(user):
    """Login as the user."""
    if isinstance(user, str):
        user = get_user_model().objects.get(username=user)

    connection = OAuthConnection.objects.get(user=user, provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    return Github(connection.access_token)


def login_as_installation(github_integration, installation):
    """Login as installation"""
    access_token = github_integration.get_access_token(installation.id)
    return Github(access_token.token)


def check_org_membership(username, org):
    try:
        gh = login_as_user(username)
        user = gh.get_user(username)
        org_object = gh.get_organization(org)
        org_object.has_in_members(user)
        return True
    except:
        return False
