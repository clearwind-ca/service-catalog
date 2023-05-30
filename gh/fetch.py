import logging
from urllib.parse import urlparse

import json5 as json
from github import GithubException, UnknownObjectException

from catalog.errors import NoEntryFound, NoRepository, SchemaError

from .user import login_as_app, login_as_installation

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
        except (UnknownObjectException, GithubException):
            # This means the file is not found in the repo and we go onto the next one.
            continue

    nice_paths = ", ".join([f"`{p}`" for p in file_paths])
    raise NoEntryFound(
        f"Fetching of service JSON file failed. No file in: `{repo.full_name}`. Tried in these locations: {nice_paths}."
    )


def url_to_nwo(url):
    path = urlparse(url).path
    # Remove the leading slash.
    if path.startswith("/"):
        path = path[1:]

    if path.endswith("/"):
        path = path[:-1]

    if path.count("/") != 1:
        raise ValueError(f"Can't parse {url}.")

    organization, repo = path.split("/")
    return organization, repo


def get_repo(gh, repo):
    try:
        repo = gh.get_repo(repo)
    except UnknownObjectException:
        raise NoRepository(f"Unable to access the repository at: `{repo}`.")

    return repo


def get(source):
    organization, repo = url_to_nwo(source.url)
    repo = get_repo_installation(organization, repo)

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


def get_deployments(source):
    org, repo = url_to_nwo(source.url)
    repo = get_repo_installation(org, repo)
    return repo.get_deployments()


def get_repo_installation(org_name, repo_name):
    gh = login_as_app()
    try:
        installation = gh.get_repo_installation(org_name, repo_name)
        gh_installation = login_as_installation(gh, installation)
        return gh_installation.get_repo(f"{org_name}/{repo_name}")
    except UnknownObjectException:
        raise NoRepository(
            f"GitHub app is unable to access the repository: `{org_name}/{repo_name}`."
        )
    

def get_repositories(org_name):
    gh = login_as_app()
    repos = []
    for installation in gh.get_installations():
        if installation.target_type == "Organization":
            if installation.raw_data["account"]["login"] != org_name:
                break

            gh_installation = login_as_installation(gh, installation)
            try:
                org = gh_installation.get_organization(org_name)
            except UnknownObjectException:
                raise NoRepository(f"Unable to access the organization: `{org_name}`.")

            installations = org.get_installations()
            for org_install in installations:
                for repo in org_install.get_repos():
                    repos.append(repo)

    return repos


def get_orgs():
    gh = login_as_app()
    orgs = []
    for installation in gh.get_installations():
        if installation.target_type == "Organization":
            account = installation.raw_data["account"]
            gh_installation = login_as_installation(gh, installation)
            org = gh_installation.get_organization(account["login"])
            orgs.append(
                {
                    "login": account["login"],
                    "html_url": account["html_url"],
                    "account": account,
                    "installation": installation,
                    "raw_data": org.raw_data,
                }
            )
    return orgs
