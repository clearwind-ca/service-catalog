import os

from github import Github


def login_as_user(user):
    """Login as the user."""
    connection = user.oauth_connections.get(provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    return Github(connection.access_token)


def login_as_app():
    """Login as the app."""
    return Github(app_id=os.environ["GITHUB_CLIENT_ID"])


def get_repo_list(user):
    """Get the list of repos for the user."""
    gh = login_as_app()
    import pdb

    pdb.set_trace()
    return gh.get_repos()
