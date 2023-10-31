import json
import logging

from events.models import Event
from web.shortcuts import get_object_or_None

logger = logging.getLogger(__name__)


def handle(request):
    data = json.loads(request.body)
    existing = get_object_or_None(Event, external_id=data["_id"])
    if not existing:
        Event.objects.create(
            name=data["name"],
            type=data["kind"],
            description=data["title"] + "\n\n" + data["description"],
            customers=False,
            external_id=data["_id"],
            url="https://app.launchdarkly.com" + data["_links"]["site"]["href"],
            source="LaunchDarkly",
        )
    else:
        logger.info("Event already exists, skipping")
