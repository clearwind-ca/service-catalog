from .user import login_as_app


def get_perms():
    """Get permissions for the app."""
    gh = login_as_app()
    installations = {}
    for installation in gh.get_installations():
        installations[installation.id] = installation.raw_data["permissions"]
    return installations
