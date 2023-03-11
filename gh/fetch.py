import json
import logging

from github import Github, GithubException, UnknownObjectException

logging.getLogger("github").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def login_as_user(user):
    """Login as the user."""
    connection = user.oauth_connections.get(provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    gh = Github(connection.access_token)
    return gh.get_user()


file_paths = [
    "catalog.json",
    "service.json",
    ".github/catalog.json",
    ".github/service.json",
]


def get_file(repo):
    for path in file_paths:
        try:
            return repo.get_contents("catalog.json").decoded_content.decode("utf-8")
        except UnknownObjectException as error:
            logger.info(f"File not found: {path} from: {repo.full_name}")
            continue
        except GithubException:
            logger.info(f"Error in: {path} from: {repo.full_name}")
            raise

    raise GithubException("No file found")


def get(user, source):
    gh_user = login_as_user(user)
    repo = gh_user.get_repo(source.name.split("/")[1])
    entry = get_file(repo)
    data = json.loads(entry)
    return data
