import json
import logging
import os

import jsonschema
from django.conf import settings
from github import Github, GithubException, UnknownObjectException
from jsonschema import ValidationError

from catalog.errors import NoEntryFound, NoRepository, SchemaError

logging.getLogger("github").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

from oauthlogin.models import OAuthConnection


def login_as_user(user):
    """Login as the user."""
    connection = OAuthConnection.objects.get(user=user, provider_key="github")
    if connection.access_token_expired():
        connection.refresh_access_token()

    return Github(connection.access_token)


file_paths = [
    "catalog.json",
    ".github/catalog.json",
]


def get_file(repo):
    for path in file_paths:
        try:
            return repo.get_contents(path).decoded_content.decode("utf-8")
        except UnknownObjectException:
            logger.info(f"File not found: {path} from: {repo.full_name}")
            continue
        except GithubException:
            logger.info(f"Error in: {path} from: {repo.full_name}")
            raise

    nice_paths = ", ".join([f"`{p}`" for p in file_paths])
    raise NoEntryFound(
        f"Fetching of service definition failed. No file found in: `{repo.full_name}`. Tried in these locations: {nice_paths}."
    )


def get(user, source):
    gh = login_as_user(user)
    organization, repo = source.name.split("/")
    try:
        user = gh.get_user(organization)
    except UnknownObjectException:
        raise NoRepository(
            f"Unable to access the user or organization: `{organization}`."
        )

    try:
        repo = repo = user.get_repo(repo)
    except UnknownObjectException:
        raise NoRepository(f"Unable to access the repository at: `{repo}`.")

    entry = get_file(repo)

    try:
        data = json.loads(entry)
    except json.JSONDecodeError:
        raise SchemaError(f"Unable to decode the JSON in: `{repo.full_name}`.")

    schema = get_schema()
    try:
        jsonschema.validate(data, schema)
    except ValidationError as error:
        raise SchemaError(
            f"Errors validating the schema in: `{repo.full_name}`. The error is: `{error.message}`."
        )

    return data


def get_schema():
    if not os.path.exists(settings.SERVICE_SCHEMA):
        raise ValueError(f"No schema file found at: {settings.SERVICE_SCHEMA}")

    with open(settings.SERVICE_SCHEMA, "r") as schema_file:
        return json.load(schema_file)


def validate(user, source):
    data = get(user, source)
    schema = get_schema()
    jsonschema.validate(data, schema)
