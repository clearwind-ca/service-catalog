# Generated by Django 4.1.7 on 2023-04-29 00:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Check",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True, help_text="Markdown is supported.")),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("hourly", "Hourly"),
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("ad-hoc", "Ad hoc"),
                        ],
                        default="daily",
                        help_text="How often this check will be run.",
                        max_length=10,
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="CheckResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        choices=[
                            ("pass", "Pass"),
                            ("warning", "Warning"),
                            ("fail", "Fail"),
                            ("error", "Error"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=10,
                    ),
                ),
                ("message", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("sent", "Sent"),
                            ("timed-out", "Timed out"),
                            ("error", "Error"),
                            ("completed", "Completed"),
                        ],
                        default="sent",
                        max_length=10,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "health_check",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="health.check"
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="services.service"
                    ),
                ),
            ],
        ),
    ]
