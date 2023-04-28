# Generated by Django 4.1.7 on 2023-04-28 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0008_alter_event_customers_alter_event_start"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="status",
            field=models.CharField(
                blank=True,
                help_text="Any external status for this event.",
                max_length=255,
                null=True,
                verbose_name="External status",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="description",
            field=models.TextField(blank=True, help_text="Markdown is supported.", null=True),
        ),
        migrations.AlterField(
            model_name="event",
            name="type",
            field=models.CharField(help_text="The type of event.", max_length=100),
        ),
    ]
