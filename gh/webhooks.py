import hashlib
import hmac
import json
import logging
import os

import requests
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from events.models import Event
from services.models import Source
from web.shortcuts import get_object_or_None

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhooks(request):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        raise ImproperlyConfigured("GITHUB_WEBHOOK_SECRET is not set")

    if "HTTP_X_HUB_SIGNATURE" not in request.META:
        return HttpResponseBadRequest("Request does not contain X-GITHUB-SIGNATURE header")
    if "HTTP_X_GITHUB_EVENT" not in request.META:
        return HttpResponseBadRequest("Request does not contain X-GITHUB-EVENT header")

    digest_name, signature = request.META["HTTP_X_HUB_SIGNATURE"].split("=")
    if digest_name != "sha1":
        return HttpResponseBadRequest(
            "Unsupported X-HUB-SIGNATURE digest mode found: {}".format(digest_name)
        )

    mac = hmac.new(secret.encode("utf-8"), msg=request.body, digestmod=hashlib.sha1)

    if not hmac.compare_digest(mac.hexdigest(), signature):
        return HttpResponseBadRequest("Invalid X-HUB-SIGNATURE header found")

    event = request.META["HTTP_X_GITHUB_EVENT"]
    if event not in events:
        return HttpResponseBadRequest("Unsupported X-GITHUB-EVENT header found: {}".format(event))

    payload = json.loads(request.body.decode("utf-8"))
    response = events[event](payload) or {"status": "ok"}
    return JsonResponse(response)


def handle_deployment(payload):
    for service in find_service(payload, "deployment"):
        status = requests.get(payload["deployment"]["statuses_url"]).json()[0]["state"]
        description = payload["deployment"]["description"]
        if not description:
            description = f'Deployment of {service.name} to {payload["deployment"]["environment"]}'
        event = Event.objects.create(
            name=f'Deployment of {service.name} to {payload["deployment"]["environment"]}',
            type="deployment",
            customers=payload["deployment"]["environment"] == "production",
            active=True,
            description=description,
            status=status,
            source="GitHub",
            url=payload["deployment"]["url"],
            external_id=payload["deployment"]["id"],
        )
        event.services.add(service)


def find_service(payload, webhook_type):
    repository = payload["repository"]["html_url"]
    source = get_object_or_None(Source, url=repository)
    if not source:
        logger.info(f"Skipping {webhook_type} webhook, no source found for {repository}")
        return

    for service in source.services.all():
        if not service.active:
            logger.info(f"Skipping release webhook inactive service {service}")
            continue

        if not service.events or "releases" not in service.events:
            logger.info(
                f"Skipping release webhook service, {service} does not have `releases` in events."
            )
            continue
        
        yield service


def handle_release(payload):
    if payload["action"] not in ["published", "unpublished"]:
        logger.info(f"Skipping release webhook, action {payload['action']} not supported")
        return

    for service in find_service(payload, "release"):
        default_msg = f'{service.name}: {payload["release"]["name"]} {payload["action"]}'
        description = payload["release"]["body"]
        if not description:
            description = default_msg
        event = Event.objects.create(
            name=default_msg,
            type="release",
            customers=not payload["release"]["prerelease"],
            active=not payload["release"]["draft"],
            description=description,
            status=payload["action"],
            source="GitHub",
            url=payload["release"]["html_url"],
            external_id=payload["release"]["id"],
        )
        event.services.add(service)



events = {
    "deployment": handle_deployment,
    "release": handle_release,
}
