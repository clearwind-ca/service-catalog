from .user import login_as_app


def get_details():
    """Get permissions and events for the app."""
    gh = login_as_app()
    installations = {}
    for installation in gh.get_installations():
        installations[installation.id] = {
            "permissions": installation.raw_data["permissions"],
            "events": installation.raw_data["events"],
            "html_url": installation.raw_data["html_url"],
        }
    return installations
