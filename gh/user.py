import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from github import Github, GithubIntegration, enable_console_debug_logging
from oauthlogin.models import OAuthConnection

logger = logging.getLogger(__name__)

if settings.GITHUB_DEBUG:
    enable_console_debug_logging()


def login_as_app():
    """Login as the app."""
    if not os.environ.get("GITHUB_APP_ID") or not os.environ.get("GITHUB_PEM"):
        raise ImproperlyConfigured("GITHUB_APP_ID and GITHUB_PEM must be set.")
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
        return org_object.has_in_members(user)
    except ObjectDoesNotExist:
        logger.error(f"Check-Org-Membership: No user object: {username}")
        return False
    except OAuthConnection.DoesNotExist:
        logger.error(f"Check-Org-Membership: No OAuthConnection for user: {username}")
        return False
    except:
        logger.error(f"Check-Org-Membership: Error for user: {username}")
        return False
