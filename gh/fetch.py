import json
import logging
from urllib.parse import urlparse

from github import GithubException, UnknownObjectException

from catalog.errors import NoEntryFound, NoRepository, SchemaError

from .user import login_as_user

logger = logging.getLogger(__name__)

file_paths = [
    "catalog.json",
    "service.json",
    ".service-catalog/catalog.json",
    ".github/catalog.json",
]


def get_contents(repo, path):
    """
    Actually get the file contents.
    """
    return json.loads(repo.get_contents(path).decoded_content.decode("utf-8"))


def get_file(repo, path):
    """
    Get a file from a single path.
    """
    try:
        return {"path": path, "contents": get_contents(repo, path)}
    except UnknownObjectException:
        logger.info(f"File not found: {path} from: {repo.full_name}")
        raise
    except GithubException:
        logger.info(f"Error in: {path} from: {repo.full_name}")
        raise
    except json.JSONDecodeError:
        raise SchemaError(f"Unable to decode the JSON in: `{repo.full_name}`.")


def get_file_from_list(repo, paths):
    """
    Get a file from a list of possible paths, useful for the first lookup.
    """
    for path in paths:
        try:
            return get_file(repo, path)
        except UnknownObjectException:
            # This means the file is not found in the repo and we go onto the next one.
            continue

    nice_paths = ", ".join([f"`{p}`" for p in file_paths])
    raise NoEntryFound(
        f"Fetching of service JSON file failed. No file in: `{repo.full_name}`. Tried in these locations: {nice_paths}."
    )


def get(user, source):
    gh = login_as_user(user)
    path = urlparse(source.url).path
    # Remove the leading slash.
    if path.startswith("/"):
        path = path[1:]

    organization, repo = path.split("/")
    try:
        user = gh.get_user(organization)
    except UnknownObjectException:
        raise NoRepository(f"Unable to access the user or organization: `{organization}`.")

    try:
        repo = user.get_repo(repo)
    except UnknownObjectException:
        raise NoRepository(f"Unable to access the repository at: `{repo}`.")

    results = []
    already_fetched = []

    def recursive_get_files(paths):
        for file in paths:
            # Try and prevent recursion, just silently skip.
            if file in already_fetched:
                continue
            already_fetched.append(file)
            result = get_file(repo, file)
            results.append(result)
            recursive_get_files(result["contents"].get("files", []))

    result = get_file_from_list(repo, file_paths)
    already_fetched.append(result["path"])
    results.append(result)
    recursive_get_files(result["contents"].get("files", []))
    return results
