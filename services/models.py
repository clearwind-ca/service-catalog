from urllib.parse import urlparse

from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse

from gh.fetch import url_to_org
from health.models import Check, CheckResult


class Service(models.Model):
    """
    This is the core to the system, a service is an entity of whatever shape and
    size that you would like it to be.
    """

    # Core fields within a service, these are key data points and get their own fields.
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    # A description of the service, used in the detail page. Markdown is supported.
    description = models.TextField()
    path = models.CharField(max_length=255)
    # Up to the user to define this, some tag that makes sense within their organisation.
    type = models.CharField(max_length=100, null=True)

    # From 1 to 10, where 1 is the highest priority and 10 is the lowest.
    priority = models.IntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    active = models.BooleanField(default=True)

    source = models.ForeignKey("Source", on_delete=models.PROTECT, related_name="services")
    dependencies = models.ManyToManyField("self", blank=True, symmetrical=False)

    # Whilst important these fields are dramatically going to vary depending upon the
    # service, the company and the other tools used. As such they are stored as JSON fields
    # to give the most flexibility.
    #
    # This is a JSON object, or a Python dictionary of key/value pairs.
    meta = models.JSONField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    events = models.JSONField(blank=True, null=True)

    # Just store the raw file too.
    raw_data = models.JSONField(blank=True, null=True)

    def logs(self):
        return LogEntry.objects.get_for_object(self)

    def dependents(self):
        return Service.objects.filter(dependencies=self)

    def save(self, *args, **kwargs):
        self.slug = slugify_service(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("services:service-detail", kwargs={"slug": self.slug})

    def results(self):
        return CheckResult.objects.filter(service=self)

    def latest_results(self):
        """Return the latest results for a service."""
        checks = Check.objects.filter(active=True)
        results = CheckResult.objects.filter(service=self).order_by("created")
        checks_with_results = []
        for check in checks:
            checks_with_results.append(
                {"check": check, "last": results.filter(health_check=check).last()}
            )
        return checks_with_results


class Source(models.Model):
    """
    The place that the service catalog data has came from. For example the GitHub repo
    containing the file.
    """

    name = models.CharField(max_length=100)
    url = models.CharField(
        max_length=255,
        verbose_name="Repository URL",
        help_text="The URL to the repository on GitHub that contains the service catalog files.",
        unique=True,
    )
    slug = models.SlugField(max_length=255, unique=True)

    active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    org = models.ForeignKey(
        "Organization",
        on_delete=models.PROTECT,
        related_name="sources",
        null=True,
        blank=True,
    )

    def logs(self):
        return LogEntry.objects.get_for_object(self)

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_source(self.url)

        # Both https://github.com/org/repo/ and https://github.com/org/repo are valid,
        # but GitHub API only uses the latter version, so let's normalize and remove the trailing slash
        # if the repository has been added manually or through the API.
        if self.url.endswith("/"):
            self.url = self.url[:-1]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("services:source-detail", kwargs={"slug": self.slug})


class Organization(models.Model):
    """
    An organization which then has sources.
    """

    name = models.CharField(max_length=255)
    auto_add_sources = models.BooleanField(
        default=True, help_text="Automatically add sources from the organization."
    )
    url = models.CharField(
        max_length=255,
        verbose_name="Organization URL",
        unique=True,
    )

    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    raw_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = url_to_org(self.url)
        super().save(*args, **kwargs)


def slugify_service(name):
    return slugify(name)


def slugify_source(url):
    return slugify(urlparse(url).path.replace("/", "-"))


auditlog.register(Organization)
auditlog.register(Service)
auditlog.register(Source)
