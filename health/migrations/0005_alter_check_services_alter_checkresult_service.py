# Generated by Django 4.1.10 on 2023-10-01 15:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0008_alter_service_type"),
        ("health", "0004_alter_check_services"),
    ]

    operations = [
        migrations.AlterField(
            model_name="check",
            name="services",
            field=models.ManyToManyField(
                blank=True,
                help_text="If this health check is limited to some services, select them here.",
                related_name="health_checks",
                to="services.service",
            ),
        ),
        migrations.AlterField(
            model_name="checkresult",
            name="service",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="services.service",
            ),
        ),
    ]