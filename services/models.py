from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify

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
    service_type = models.CharField(max_length=100)

    # From 1 to 10, where 1 is the highest priority and 10 is the lowest.
    service_level = models.IntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    is_active = models.BooleanField(default=True)

    source = models.ForeignKey("Source", on_delete=models.CASCADE, related_name="src")
    dependencies = models.ManyToManyField("self", blank=True, symmetrical=False)

    # Whilst important these fields are dramatically going to vary depending upon the
    # service, the company and the other tools used. As such they are stored as JSON fields
    # to give the most flexibility.
    #
    # Ownership could teams, lists of people. It could also include stakeholders.
    ownership = models.JSONField(blank=True, null=True)
    # Metrics, definitions, dashboards and SLAs are likely links to other services.
    metrics = models.JSONField(blank=True, null=True)
    # Support is the place for on-call, support, rotations etc.
    support = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Source(models.Model):
    """
    The place that the service catalog data has came from. For example the GitHub repo 
    containing the file.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    service = models.CharField(max_length=1, choices=(("G", "GitHub"),))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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