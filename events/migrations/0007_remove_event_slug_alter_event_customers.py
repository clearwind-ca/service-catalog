# Generated by Django 4.1.7 on 2023-04-26 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0006_remove_event_end_date_remove_event_end_time_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="slug",
        ),
        migrations.AlterField(
            model_name="event",
            name="customers",
            field=models.BooleanField(
                default=False,
                help_text="Whether this event is impacts customers of the service.",
                verbose_name="Impacts customers",
            ),
        ),
    ]