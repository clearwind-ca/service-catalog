from catalog.celery import app
from events.models import Event
from gh import fetch
from services.models import Service
from web.shortcuts import get_object_or_None


@app.task
def get_deployments(service_slug):
    service = Service.objects.get(slug=service_slug)
    deployments = fetch.get_deployments(service.source)

    # Limit to the last 20 deployments per repo, for now.
    for deployment in deployments[:20]:
        statuses = deployment.get_statuses()
        if not statuses:
            continue
        latest_status = None
        for new_status in statuses:
            new_status = deployment.get_status(new_status.id)
            if not latest_status:
                latest_status = new_status
            elif new_status.created_at > latest_status.created_at:
                latest_status = new_status

        existing = get_object_or_None(Event, external_id=deployment.id)
        if existing:
            if existing.status != latest_status:
                existing.status = latest_status.state
                existing.save()
            continue

        description = f"There was a deployment to {deployment.environment} by {deployment.creator.login}. For more information see: {service.source.url}/deployments."
        event = Event(
            type="Deployment",
            name=f"Deploy to {deployment.environment}",
            description=description,
            source="GitHub deployment",
            external_id=deployment.id,
            url=deployment.url,
            status=latest_status.state,
            start=deployment.created_at,
        )
        event.save()
        event.services.set([service])
        event.save()


@app.task
def get_all_active_deployments():
    for service in Service.objects.filter(active=True):
        if service.events and "deployments" in service.events:
            get_deployments.delay(service.slug)
