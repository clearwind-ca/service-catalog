from datetime import timedelta

from django.utils import timezone

from catalog.celery import app
from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service


def should_run(check, service, quiet=False):
    now = timezone.now()
    frequency = check.frequency
    if frequency not in ["hourly", "daily", "weekly"]:
        return False

    recent_result = (
        CheckResult.objects.filter(health_check=check, service=service).order_by("-created").first()
    )

    # If this has never been run, then we should run it.
    if recent_result is None:
        return True

    most_recent = recent_result.created

    # If this has been run more than an hour ago, then we should run it.
    if frequency == "hourly":
        if (now - most_recent).seconds > 3600:
            return True

    elif frequency == "daily":
        if (now - most_recent).days > 0:
            return True

    elif frequency == "weekly":
        if (now - most_recent).days >= 7:
            return True

    if not quiet:
        print(f"Check {check.slug} at frequency {frequency} has been run recently, skipping.")

    return False


@app.task
def send_to_github(check_slug, service_slug):
    check = Check.objects.get(slug=check_slug)
    service = Service.objects.get(slug=service_slug)
    result = CheckResult.objects.create(
        health_check=check,
        status="sent",
        service=service,
    )
    try:
        send.dispatch(result)
    except (SendError, NoRepository) as error:
        # Fatal error, they are all going to fail.
        # Should we log here?
        result.status = "error"
        result.save()
        raise error


@app.task
def send_active_to_github():
    check_queryset = Check.objects.filter(active=True)
    for check in check_queryset:

        if check.limit == "all":
            for service in Service.objects.filter(active=True):
                if should_run(check, service):
                    send_to_github.delay(check.slug, service.slug)
        
        if check.limit == "some":
            for service in check.services.all():
                if should_run(check, service):
                    send_to_github.delay(check.slug, service.slug)

        if check.limit == "none":
            if should_run(check):
                send_to_github.delay(check.slug)


@app.task
def timeout(ago):
    check_queryset = CheckResult.objects.filter(
        updated__lt=timezone.now() - timedelta(hours=ago),
        status__in=["sent"],
    )
    for check in check_queryset:
        check.status = "timed-out"
        check.save()
