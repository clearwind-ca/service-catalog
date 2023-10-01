from django.core.exceptions import ImproperlyConfigured

from .user import login_as_app, login_as_installation


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


def get_orgs():
    """Return the orgs that the app is installed on."""
    try:
        gh = login_as_app()
    except ImproperlyConfigured:
        return []

    orgs = []
    for installation in gh.get_installations():
        if installation.target_type == "Organization":
            gh_installation = login_as_installation(gh, installation)
            org = gh_installation.get_organization(installation.raw_data["account"]["login"])
            orgs.append(org)
    return orgs
