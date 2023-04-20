from django.db import models
from django.template.defaultfilters import slugify

FREQUENCY_CHOICES = (
    ("hourly", "Hourly"),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("ad-hoc", "Ad hoc"),
)


class Check(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, help_text="Markdown is supported.")

    frequency = models.CharField(max_length=10, default="daily", choices=FREQUENCY_CHOICES)

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


# The status of sending the check result to the service.
STATUS_CHOICES = (
    ("sent", "Sent"),  # We sent the status to the service.
    ("timed-out", "Timed out"),  # The service timed out, so we gave up on it.
    ("error", "Error"),  # There was an error sending the status to the service, so it never got it.
    (
        "completed",
        "Completed",
    ),  # The service got the status and completed it.
)

# The actual result that the check returns.
RESULT_CHOICES = (
    ("pass", "Pass"),  # The check passed, all is good.
    ("warning", "Warning"),  # Something is not quite right, but not bad enough to fail.
    ("fail", "Fail"),  # The check failed, something is wrong.
    ("error", "Error"),  # The service got the check, but there was an error running the check.
    ("unknown", "Unknown"),  # Default status, we've sent it but haven't heard back yet.
)


class CheckResult(models.Model):
    service = models.ForeignKey(to="services.Service", on_delete=models.CASCADE)
    health_check = models.ForeignKey(Check, on_delete=models.CASCADE)

    # How well the service is doing with this health check.
    result = models.CharField(max_length=10, default="unknown", choices=RESULT_CHOICES)
    # Any message that is returned by the health check.
    message = models.TextField(blank=True)

    # The state within the health check process.
    status = models.CharField(max_length=10, default="sent", choices=STATUS_CHOICES)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service} - {self.health_check} - {self.result}"

    def save(self, *args, **kwargs):
        # Ensure that once we've completed a check, we can't change it.
        if self.status == "completed":
            raise ValueError("Cannot alter a completed check result.")

        # If we've received a result, we've completed the check.
        if self.result != "unknown" and self.status == "sent":
            self.status = "completed"

        super().save(*args, **kwargs)
