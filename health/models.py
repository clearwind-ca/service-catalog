from django.db import models
from django.template.defaultfilters import slugify

FREQUENCY_CHOICES = (
    ("hourly", "Hourly"),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("ad hoc", "Ad hoc"),
)


class Check(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    frequency = models.CharField(max_length=10, default="D", choices=FREQUENCY_CHOICES)

    active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensure that changing the name does not change the slug.
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


STATUS_CHOICES = (
    ("sent", "Sent"),
    ("failed", "Failed"),
    ("timed out", "Timed out"),
    ("completed", "Completed"),
)

RESULT_CHOICES = (
    ("pass", "Pass"),
    ("warning", "Warning"),
    ("fail", "Fail"),
    ("error", "Error"),
    ("unknown", "Unknown"),
)


class CheckResult(models.Model):
    service = models.ForeignKey(to="services.Service", on_delete=models.CASCADE)
    health_check = models.ForeignKey(Check, on_delete=models.CASCADE)

    # How well the service is doing with this health check.
    result = models.CharField(max_length=10, default="unknown", choices=RESULT_CHOICES)
    # Any message that is returned by the health check.
    message = models.TextField(blank=True)

    # The state within the health check process.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service} - {self.health_check} - {self.result}"
