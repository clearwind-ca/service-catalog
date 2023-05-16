from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

models = {
    "members": ["check", "checkresult", "event", "organization", "service", "source", "token"],
    "public": ["check", "checkresult", "event", "organization", "service", "source"],
}
prefixes = {"members": ("add", "change", "delete", "view"), "public": ("view")}


def get_filtered_content_types(models):
    for obj in ContentType.objects.all():
        if obj.model not in models:
            continue
        yield obj


def setup_group(name=None):
    assert name in ["members", "public"]
    to_add = []
    for ct in get_filtered_content_types(models[name]):
        for perm in Permission.objects.filter(content_type__pk=ct.pk):
            if perm.codename.startswith(prefixes[name]):
                to_add.append(perm)

    group, _ = Group.objects.get_or_create(name=name)
    group.permissions.set(to_add)
