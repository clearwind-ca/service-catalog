# Generated by Django 4.1.7 on 2023-04-19 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("health", "0004_remove_checkresult_score_checkresult_result_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="check",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
