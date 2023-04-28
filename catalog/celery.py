import os

from django.conf import settings
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catalog.settings")
app = Celery("catalog")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.timezone = settings.TIME_ZONE
app.conf.beat_schedule = {
    'send-active-checks-to-github': {
        'task': 'health.tasks.send_active_to_github',
        'schedule': 60 * 5, # Every 5 minutes.
        'args': (os.environ.get("CRON_USER"),),
    }
}
