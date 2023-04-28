from datetime import timedelta

from auditlog.models import LogEntry
from django.utils import timezone

from catalog.celery import app


@app.task
def truncate(ago):
    queryset = LogEntry.objects.filter(timestamp__lt=timezone.now() - timedelta(days=ago))
    queryset.delete()
