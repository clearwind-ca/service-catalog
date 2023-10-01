import json

from django.conf import settings
from github import GithubException, UnknownObjectException

from catalog.errors import FileAlreadyExists
from gh.fetch import get_repo_installation

default_branch_name = "catalog"


def check_can_create(repo, default_branch, filename, branch=default_branch_name):
    """Do some checks that we can actually create the file."""
    sha_latest_commit = default_branch.commit.sha
    try:
        repo.get_contents(filename, ref=default_branch.name)
    except UnknownObjectException:
        # There's no existing file, so we can continue.
        pass
    else:
        # Let's just bail at this point.
        raise FileAlreadyExists(
            f"Branch: `{default_branch.name}` already contains file: `{filename}`."
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
            repo.get_contents(filename, ref=branch)
        except UnknownObjectException:
            # There's no catalog.json there, so we can continue.
            pass
        else:
            # The file already exists, so if we branch, we'll get into conflict.
            # At the moment we are focusing on creating files, not updating them.
            raise FileAlreadyExists(f"Branch: `{branch}` already contains file: {filename}.")


def get_action_blurb(type, check):
    # pyyaml can do this, but has a habit of re-ordering things to make it hard to read.
    if type == "examine-json":
        return f"""name: Catalog Check - {check.name}
run-name: Catalog check ${{{{ github.event.client_payload.check }}}} on ${{{{ github.event.client_payload.service }}}}
on:
  repository_dispatch:
    types: [{check.slug}]

jobs:
  meta:
    # This assumes that the service catalog token is a secret that has been added and is available to this repository.
    env:
      SERVICE_CATALOG_TOKEN: ${{{{ secrets.SERVICE_CATALOG_TOKEN }}}}
    runs-on: ubuntu-latest
    steps:
    
    # Extract the payload from the event.
    - uses: clearwind-ca/get-payload@main

    # Do something here with the payload sent from the catalog server.
    # You will find the JSON at /tmp/service-catalog-payload.json
    # You will find the catalog.json inside the JSON with the key `catalog.json`
    
    # Send the result back to the server.
    - uses: clearwind-ca/send-result@main
"""

    elif type == "checkout-repo":
        return f"""name: Catalog Check - {check.name}
run-name: Catalog check ${{{{ github.event.client_payload.check }}}} on ${{{{ github.event.client_payload.service }}}}
on:
  repository_dispatch:
    types: [{check.slug}]

jobs:
  meta:
    # This assumes that the service catalog token is a secret that has been added and is available to this repository.
    env:
      SERVICE_CATALOG_TOKEN: ${{{{ secrets.SERVICE_CATALOG_TOKEN }}}}
    
    # Checkout the repository as defined in the payload.
    - uses: actions/checkout@v3
      with:
        repository: ${{ github.event.client_payload.repository }}
    
    # Do something here with the repository.
    
    # Send the result back to the server.
    - uses: clearwind-ca/send-result@main
"""
    else:
        raise NotImplementedError(f"Unknown action type: {type}")


def create_action_file(org_name, repo_name, data, check):
    repo = get_repo_installation(org_name, repo_name)
    yaml = get_action_blurb(data["type"], check)

    branch = f"{default_branch_name}-{check.slug}"
    default_branch = repo.get_branch(repo.default_branch)
    filename = f".github/workflows/catalog-action-{check.slug}.yml"
    check_can_create(repo, default_branch, filename, branch=branch)

    msg = f"Initial catalog Action creation"
    body = f"""👋 This is an automated pull request to create an Action file for the catalog.
    
It comes from the [service]({settings.SERVER_URL}) and it was populated this with some simple defaults from this repository.

As of creation, it won't have enough to do anything useful, that will needed to be added by someone. When that's done, you can probably replace these sentances with something that explains what it does.
"""
    repo.create_file(filename, msg, yaml, branch=branch)
    pull = repo.create_pull(title=msg, body=body, head=branch, base=default_branch.name)
    return pull


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
    text = comment + json.dumps(file, indent=2)
    default_branch = repo.get_branch(repo.default_branch)

    check_can_create(repo, default_branch, "catalog.json")

    msg = f"Initial catalog file creation"
    body = f"""👋 This is an automated pull request to create a catalog file for this repository.

It comes from the [service]({settings.SERVER_URL}) and it was populated this with some simple defaults from this repository. Please review the required `priority` field, where `1` is the highest priority and `10` is the lowest priority.

The file is validated against [the schema]({settings.SERVICE_SCHEMA}). More information on the catalog file is [available](https://github.com/clearwind-ca/service-catalog/blob/main/docs/getting-started.md#service)

If you'd like to change or add to the contents of this file, please do so and when ready merge this pull request.
"""
    repo.create_file("catalog.json", msg, text, branch=default_branch_name)
    pull = repo.create_pull(
        title=msg, body=body, head=default_branch_name, base=default_branch.name
    )
    return pull
