from catalog.celery import app
from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service


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
