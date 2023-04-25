# Generated by Django 4.1.7 on 2023-04-25 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("services", "0005_alter_source_url"),
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
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField(blank=True, null=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("deploy", "Deployment"),
                            ("release", "Release"),
                            ("upgrade", "Upgrade"),
                            ("downgrade", "Downgrade"),
                            ("rollback", "Rollback"),
                            ("reboot", "Reboot"),
                            ("migration", "Migration"),
                            ("backup", "Backup"),
                            ("restore", "Restore"),
                            ("snapshot", "Snapshot"),
                            ("scale", "Scale"),
                            ("provision", "Provision"),
                            ("deprovision", "Deprovision"),
                            ("configuration", "Configuration"),
                            ("patch", "Patch"),
                            ("incident", "Incident"),
                            ("maintenance", "Maintenance"),
                            ("other", "Other"),
                        ],
                        max_length=100,
                    ),
                ),
                ("description", models.TextField()),
                ("external_source", models.CharField(blank=True, max_length=255, null=True)),
                ("external_uuid", models.CharField(blank=True, max_length=255, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("services", models.ManyToManyField(blank=True, to="services.service")),
            ],
        ),
    ]
