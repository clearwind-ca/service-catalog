from auditlog.registry import auditlog
from django.db import models
from django.template.defaultfilters import slugify
from datetime import datetime

EVENT_TYPES = (
    ("backup", "Backup"),
    ("configuration", "Configuration"),
    ("deploy", "Deployment"),
    ("deprovision", "Deprovision"),
    ("downgrade", "Downgrade"),
    ("incident", "Incident"),
    ("maintenance", "Maintenance"),
    ("migration", "Migration"),
    ("patch", "Patch"),
    ("provision", "Provision"),
    ("reboot", "Reboot"),
    ("release", "Release"),
    ("restore", "Restore"),
    ("rollback", "Rollback"),
    ("scale", "Scale"),
    ("snapshot", "Snapshot"),
    ("upgrade", "Upgrade"),
    ("other", "Other"),
)


class Event(models.Model):
    name = models.CharField(max_length=255)

    start = models.DateTimeField(default=datetime.now, blank=True)
    # Some events might be a point in time, in which case can be null.
    end = models.DateTimeField(
        blank=True,
        null=True,
        help_text="If the event is a singular point in time, leave the end date and time blank.",
    )

    type = models.CharField(max_length=100, choices=EVENT_TYPES, help_text="The type of event.")
    description = models.TextField(help_text="Markdown is supported.", blank=True)

    services = models.ManyToManyField(
        "services.Service", blank=True, help_text="The services affected by this event."
    )

    # Fields that external things might set.
    external_source = models.CharField(
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
    external_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="External URL",
        help_text="Any external URL for this event.",
    )

    customers = models.BooleanField(
        default=False,
        verbose_name="Impacts customers",
        help_text="Whether this event is impacts customers of the service.",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.type}"


auditlog.register(Event)
