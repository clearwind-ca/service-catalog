# Generated by Django 4.1.10 on 2023-10-01 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0008_alter_service_type"),
        ("health", "0003_check_limit_check_services"),
    ]

    operations = [
        migrations.AlterField(
            model_name="check",
            name="services",
            field=models.ManyToManyField(
                blank=True, related_name="health_checks", to="services.service"
            ),
        ),
    ]
