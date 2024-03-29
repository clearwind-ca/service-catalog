# Generated by Django 4.1.7 on 2023-04-29 00:21

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("start", models.DateTimeField(default=datetime.datetime.now)),
                (
                    "end",
                    models.DateTimeField(
                        blank=True,
                        help_text="If the event is a singular point in time, leave the end date and time blank.",
                        null=True,
                    ),
                ),
                ("type", models.CharField(help_text="The type of event.", max_length=100)),
                (
                    "description",
                    models.TextField(blank=True, help_text="Markdown is supported.", null=True),
                ),
                (
                    "customers",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this event impacts customers of the service.",
                        verbose_name="Impacts customers",
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        help_text="If the source of his event is external, enter the source.",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "external_id",
                    models.CharField(
                        blank=True,
                        help_text="Any external ID for this event.",
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name="External ID",
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        blank=True,
                        help_text="Any external URL for this event.",
                        max_length=255,
                        null=True,
                        verbose_name="External URL",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        help_text="Any external status for this event.",
                        max_length=255,
                        null=True,
                        verbose_name="External status",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "services",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The services affected by this event.",
                        to="services.service",
                    ),
                ),
            ],
        ),
    ]
