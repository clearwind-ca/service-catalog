# Generated by Django 4.1.7 on 2023-04-28 16:34

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0007_remove_event_slug_alter_event_customers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="customers",
            field=models.BooleanField(
                default=False,
                help_text="Whether this event impacts customers of the service.",
                verbose_name="Impacts customers",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="start",
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]