import base64
import json

from django.conf import settings
from django.urls import reverse
from github import UnknownObjectException

from catalog.errors import NoRepository
from health.serializers import CheckResultSerializer, CheckSerializer
from services.serializers import ServiceSerializer, SourceSerializer

from .user import login_as_user


def dispatch(user, result):
    """Send checks to GitHub as repository dispatch"""
    gh = login_as_user(user)
    try:
        repo = gh.get_repo(settings.GITHUB_CHECK_REPOSITORY)
    except UnknownObjectException:
        raise NoRepository(
            f"Unable to access the repository at: `{settings.GITHUB_CHECK_REPOSITORY}`."
        )

    data = json.dumps(
        {
            "server": {
                "url": settings.SERVER_URL,
                "endpoint": reverse("health:api-result-detail", args=[result.id]),
            },
            "check": CheckSerializer(result.health_check).data,
            "result": CheckResultSerializer(result).data,
            "service": ServiceSerializer(result.service).data,
            "source": SourceSerializer(result.service.source).data,
        }
    )
    data = base64.b64encode(data.encode("utf-8")).decode("utf-8")
    payload = {"data": data}

    res = repo.create_repository_dispatch(event_type="check", client_payload=payload)
    print(res)
