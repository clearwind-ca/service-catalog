from django.db import models
from services.models import Service
from django.template.defaultfilters import slugify

FREQUENCY_CHOICES = (
    ("H", "Hourly"),
    ("D", "Daily"),
    ("W", "Weekly"),
    ("M", "Monthly"),
    ("A", "Ad hoc")
)

class HealthCheck(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    frequency = models.CharField(max_length=2, default="D", choices=FREQUENCY_CHOICES)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensure that changing the name does not change the slug.
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

STATUS_CHOICES = (
    ("S", "Sent"),
    ("C", "Received"),
    ("F", "Failed"),
)

class HealthCheckResult(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    # How well the service is doing with this health check.
    score = models.CharField(max_length=255)
    # Any message that is returned by the health check.
    message = models.TextField(blank=True)

    # The state within the health check process.
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

