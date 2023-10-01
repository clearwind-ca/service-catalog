from datetime import timedelta

from django.utils import timezone

from catalog.celery import app
from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service


def should_run(check, service=None, quiet=False):
    now = timezone.now()
    frequency = check.frequency
    if frequency not in ["hourly", "daily", "weekly"]:
        return False

    # If there's no services defined, but you've sent a service that's a failure.
    if check.limit == "none" and service is not None:
        raise ValueError("You cannot send a service to a check that has no services defined.")

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
def send_to_github(check_slug, service_slug=None):
    check = Check.objects.get(slug=check_slug)
    service = None
    if service_slug:
        service = Service.objects.get(slug=service_slug)

    if check.limit == "none" and service is not None:
        raise ValueError("You cannot send a service to a check that has no services defined.")

    result = CheckResult.objects.create(health_check=check, status="sent", service=service)

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
        services = check.get_services()
        if services is None:
            if should_run(check):
                send_to_github.delay(check.slug)
        else:
            for service in services:
                if should_run(check, service):
                    send_to_github.delay(check.slug, service.slug)


@app.task
def timeout(ago):
    check_queryset = CheckResult.objects.filter(
        updated__lt=timezone.now() - timedelta(hours=ago),
        status__in=["sent"],
    )
    for check in check_queryset:
        check.status = "timed-out"
        check.save()
