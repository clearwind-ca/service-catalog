# Generated by Django 4.1.5 on 2023-03-09 00:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0003_service_slug"),
    ]

    operations = [
        migrations.RenameField(
            model_name="service",
            old_name="oncalls",
            new_name="support",
        ),
    ]