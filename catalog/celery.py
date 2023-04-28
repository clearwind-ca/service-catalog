import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catalog.settings")
app = Celery("catalog")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.timezone = settings.TIME_ZONE
app.conf.beat_schedule = {
    "send-active-checks-to-github": {
        "task": "health.tasks.send_active_to_github",
        "schedule": 60 * 5,  # Every 5 minutes.
        "args": (os.environ.get("CRON_USER"),),
    },
    "timeout-health-checks": {
        "task": "health.tasks.timeout",
        "schedule": 60 * 60,  # Every hour.
        "args": (6,),  # Timeout health check results older than 6 hours.
    },
    "truncate-logs": {
        "task": "systemlogs.tasks.truncate",
        "schedule": 60 * 60 * 24,  # Every 24 hours.
        "args": (30,),  # Truncate logs older than 30 days.
    },
    "refresh-active-services-from-github": {
        "task": "services.tasks.refresh_active_from_github",
        "schedule": 60 * 5,  # Every hour.
        "args": (os.environ.get("CRON_USER"),),
    },
    "get-active-services-deployments": {
        "task": "events.tasks.get_all_active_deployments",
        "schedule": 60 * 5,  # Every hour.
        "args": (os.environ.get("CRON_USER"),),
    },
}
