from json import dumps

from django.conf import settings
from github import GithubException, UnknownObjectException

from catalog.errors import FileAlreadyExists
from gh.fetch import get_repo_installation


def create_json_file(org_name, repo_name):
    repo = get_repo_installation(org_name, repo_name)
    file = {
        "name": repo.name,
        "priority": 5,
        "description": repo.description,
        "meta": {
            "github": repo.html_url,
            "issues": repo.html_url + "/issues",
        },
    }
    comment = f"""/* 
This file was created automatically by the Catalog at: {settings.SERVER_URL}
Note this file is JSON5: https://json5.org/ so can contain comments and trailing commas and more.
*/
"""
    text = comment + dumps(file, indent=2)
    default_branch = repo.get_branch(repo.default_branch)
    sha_latest_commit = default_branch.commit.sha
    branch = "catalog"
    try:
        repo.get_contents("catalog.json", ref=default_branch.name)
    except UnknownObjectException:
        # There's no catalog.json there, so we can continue.
        pass
    else:
        # The file already exists, so if we branch, we'll get into conflict.
        # At the moment we are focusing on creating files, not updating them.
        raise FileAlreadyExists(
            f"Branch: `{default_branch.name}` in: `{repo_name}` already contains file: `catalog.json`."
        )

    try:
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=sha_latest_commit)
    except GithubException as error:
        if error.data["message"] == "Reference already exists":
            # A branch already exists, so we can't create it.
            pass
        else:
            raise error

        # The file already exists on the branch.
        try:
            repo.get_contents("catalog.json", ref=branch)
        except UnknownObjectException:
            # There's no catalog.json there, so we can continue.
            pass
        else:
            # The file already exists, so if we branch, we'll get into conflict.
            # At the moment we are focusing on creating files, not updating them.
            raise FileAlreadyExists(
                f"Branch: `{branch}` in: `{repo_name}` already contains file: `catalog.json`."
            )

    msg = f"Initial catalog file creation"
    body = f"""👋 This is an automated pull request to create a catalog file for this repository.

It comes from the [service]({settings.SERVER_URL}) and it was populated this with some simple defaults from this repository. Please review the required `priority` field, where `1` is the highest priority and `10` is the lowest priority.

The file is validated against [the schema]({settings.SERVICE_SCHEMA}). More information on the catalog file is [available](https://github.com/clearwind-ca/service-catalog/blob/main/docs/getting-started.md#service)

If you'd like to change or add to the contents of this file, please do so and when ready merge this pull request.
"""
    repo.create_file("catalog.json", msg, text, branch=branch)
    pull = repo.create_pull(title=msg, body=body, head="catalog", base=default_branch.name)
    return pull
