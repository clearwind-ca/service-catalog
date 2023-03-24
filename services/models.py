from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


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
    # Up to the user to define this, some tag that makes sense within their organisation.
    type = models.CharField(max_length=100)

    # From 1 to 10, where 1 is the highest priority and 10 is the lowest.
    level = models.IntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    active = models.BooleanField(default=True)

    source = models.ForeignKey(
        "Source", on_delete=models.CASCADE, related_name="services"
    )
    dependencies = models.ManyToManyField("self", blank=True, symmetrical=False)

    # Whilst important these fields are dramatically going to vary depending upon the
    # service, the company and the other tools used. As such they are stored as JSON fields
    # to give the most flexibility.
    #
    # This is a JSON object, or a Python dictionary of key/value pairs.
    meta = models.JSONField(blank=True, null=True)

    def dependents(self):
        return Service.objects.filter(dependencies__in=[self])

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("services:service_detail", kwargs={"slug": self.slug})


class Source(models.Model):
    """
    The place that the service catalog data has came from. For example the GitHub repo
    containing the file.
    """

    HOSTS = {"G": "GitHub"}
    HOSTS_INVERTED = {v: k for k, v in HOSTS.items()}

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    host = models.CharField(max_length=1, choices=[(k, v) for k, v in HOSTS.items()])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name.replace("/", "-"))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("services:source_list")


class Schema(models.Model):
    """
    A schema is a way of defining the structure of a service. It is a way of
    defining the fields that are required and the types of those fields.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    schema = models.TextField()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
