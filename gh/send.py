import base64
import json

from django.conf import settings
from django.urls import reverse

from catalog.errors import SendError
from health.serializers import CheckResultSerializer, CheckSerializer
from services.serializers import ServiceSerializer, SourceSerializer

from .fetch import get_repo_installation, url_to_nwo


def dispatch(result):
    """Send checks to GitHub as repository dispatch"""
    repo = get_repo_installation(*url_to_nwo(settings.GITHUB_CHECK_REPOSITORY))

    # The general principle here is to send as much data as possible so that the API
    # has to do as little as possible work to call back to the service catalog to decide
    # what to do.
    data = json.dumps(
        {
            "server": {
                "url": settings.SERVER_URL,
                "endpoint": reverse("health:api-result-detail", args=[result.id]),
            },
            "check": CheckSerializer(result.health_check).data,
            "result": CheckResultSerializer(result).data,
            "service": ServiceSerializer(result.service).data if result.service else None,
            "source": SourceSerializer(result.service.source).data if result.service else None,
            "catalog.json": result.service.raw_data if result.service else None,
        }
    )
    # GitHub is assuming that the data is a string when you access the payload
    # in the action. If you send an object, you will get an error about
    # an expected mapping.
    #
    # We don't really need GitHub to do anything with data, we are just going to
    # pass it to a nice simple library to grab the payload. So in this case we'll
    # just encode the data.
    #
    # Perhaps there's a better way to do this, but this works for now.
    data = base64.b64encode(data.encode("utf-8")).decode("utf-8")
    payload = {
        "data": data,
        # Things that are really useful to have and can be accessed directly.
        "check": result.health_check.slug,
        "service": result.service.slug if result.service else None,
        "repository": "/".join(url_to_nwo(result.service.source.url)) if result.service else None,
        "server": settings.SERVER_URL,
    }

    res = repo.create_repository_dispatch(
        event_type=result.health_check.slug, client_payload=payload
    )
    if not res:
        raise SendError("Unable to dispatch repository event.")
