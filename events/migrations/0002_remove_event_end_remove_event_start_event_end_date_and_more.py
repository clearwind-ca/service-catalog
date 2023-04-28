# Generated by Django 4.1.7 on 2023-04-25 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="end",
        ),
        migrations.RemoveField(
            model_name="event",
            name="start",
        ),
        migrations.AddField(
            model_name="event",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="end_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="start_date",
            field=models.DateField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="event",
            name="start_time",
            field=models.TimeField(default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="event",
            name="description",
            field=models.TextField(blank=True, help_text="Markdown is supported."),
        ),
    ]