# Generated by Django 4.1.7 on 2023-05-02 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="source",
            name="name",
            field=models.CharField(default=None, max_length=100),
            preserve_default=False,
        ),
    ]