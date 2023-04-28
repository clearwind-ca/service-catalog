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
    }
}
