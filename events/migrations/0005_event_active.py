# Generated by Django 4.1.7 on 2023-04-25 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_event_name_event_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]