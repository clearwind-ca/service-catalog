from django.db import migrations

from web.groups import setup_group


def apply_permissions(apps, schema_editor):
    setup_group(name="members")
    setup_group(name="public")


def reverse_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    members = Group.objects.get(name="members")
    members.permissions.clear()
    members.delete()

    public = Group.objects.get(name="public")
    public.permissions.clear()
    public.delete()


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunPython(apply_permissions, reverse_permissions),
    ]
