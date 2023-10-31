import json
import logging

from events.models import Event
from web.shortcuts import get_object_or_None

logger = logging.getLogger(__name__)


def handle(request):
    """
    This is a general handler for all services that use Atlassian Statuspages.

    Atlassian use it, but so do many other companies.
    """
    data = json.loads(request.body)
    if "incident" not in data:
        logger.info("Not an incident, skipping")
        return

    existing = get_object_or_None(Event, external_id=data["incident"]["id"])
    if not existing:
        Event.objects.create(
            name=data["incident"]["name"],
            type="Incident",
            description=data["incident"]["incident_updates"][0]["body"],
            customers=False,
            start=data["incident"]["created_at"],
            end=data["incident"]["resolved_at"] or None,
            external_id=data["incident"]["id"],
            url=data["incident"]["shortlink"],
            source="Confluence",
            status=data["incident"]["status"],
        )
    else:
        if data["incident"]["resolved_at"]:
            existing.end = data["incident"]["resolved_at"]

        if data["incident"]["status"] != existing.status:
            existing.status = data["incident"]["status"]

        if data["incident_updates"][0]["body"] != existing.description:
            existing.description = data["incident_updates"][0]["body"]

        existing.save()
