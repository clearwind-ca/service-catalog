# Generated by Django 4.1.7 on 2023-04-28 20:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_rename_source_event_external_source_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="event",
            old_name="external_source",
            new_name="source",
        ),
        migrations.RenameField(
            model_name="event",
            old_name="external_url",
            new_name="url",
        ),
    ]