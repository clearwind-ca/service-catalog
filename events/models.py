from datetime import datetime

from auditlog.registry import auditlog
from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255)

    start = models.DateTimeField(default=datetime.now)
    # Some events might be a point in time, in which case can be null.
    end = models.DateTimeField(
        blank=True,
        null=True,
        help_text="If the event is a singular point in time, leave the end date and time blank.",
    )

    type = models.CharField(max_length=100, help_text="The type of event.")
    description = models.TextField(help_text="Markdown is supported.", blank=True, null=True)

    services = models.ManyToManyField(
        "services.Service", blank=True, help_text="The services affected by this event."
    )

    customers = models.BooleanField(
        default=False,
        verbose_name="Impacts customers",
        help_text="Whether this event impacts customers of the service.",
    )

    active = models.BooleanField(default=True)

    # Fields that external things might set.
    source = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="If the source of his event is external, enter the source.",
    )

    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="External ID",
        help_text="Any external ID for this event.",
    )

    url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="URL",
        help_text="Any external URL for this event.",
    )

    status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Status",
        help_text="Any external status for this event.",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.type}"


auditlog.register(Event)
