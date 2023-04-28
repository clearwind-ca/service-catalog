# Generated by Django 4.1.7 on 2023-04-25 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_remove_event_external_uuid_event_customers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="name",
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="slug",
            field=models.SlugField(default=None, max_length=100, unique=True),
            preserve_default=False,
        ),
    ]