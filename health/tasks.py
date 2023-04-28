from catalog.celery import app
from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service
from django.utils import timezone


def should_run(check, service, quiet=False):
    now = timezone.now()
    frequency = check.frequency
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

    if frequency == "daily":
        if (now - most_recent).days > 0:
            return True

    if frequency == "weekly":
        if (now - most_recent).days >= 7:
            return True

    if not quiet:
        print(f"Check {check.slug} at frequency {frequency} has been run recently, skipping.")

    return False


@app.task
def send_to_github(username, check_slug, service_slug):
    check = Check.objects.get(slug=check_slug)
    service = Service.objects.get(slug=service_slug)
    result = CheckResult.objects.create(
        health_check=check,
        status="sent",
        service=service,
    )
    try:
        # Should this use the cron user?
        send.dispatch(username, result)
    except (SendError, NoRepository) as error:
        print("here!")
        # Fatal error, they are all going to fail.
        # Should we log here?
        result.status = "error"
        result.save()
        raise error


@app.task
def send_active_to_github(username):
    if not username:
        raise ValueError("Username is required to send active checks to GitHub.")
    
    check_queryset = Check.objects.filter(active=True)
    service_queryset = Service.objects.filter(active=True)
    for check in check_queryset:
        for service in service_queryset:
            if should_run(check, service):
                send_to_github.delay(username, check.slug, service.slug)