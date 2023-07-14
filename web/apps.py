from django.apps import AppConfig
from django.db.models.signals import post_migrate

models = {
    "members": ["check", "checkresult", "event", "organization", "service", "source", "token"],
    "public": ["check", "checkresult", "event", "organization", "service", "source"],
}
prefixes = {"members": ("add", "change", "delete", "view"), "public": ("view")}


def get_filtered_content_types(models):
    from django.contrib.contenttypes.models import ContentType

    for obj in ContentType.objects.all():
        if obj.model not in models:
            continue
        yield obj


def setup_groups(**kwargs):
    from django.contrib.auth.models import Group, Permission

    for name in ["members", "public"]:
        to_add = []
        for ct in get_filtered_content_types(models[name]):
            for perm in Permission.objects.filter(content_type__pk=ct.pk):
                if perm.codename.startswith(prefixes[name]):
                    to_add.append(perm)

        group, created = Group.objects.get_or_create(name=name)
        if created:
            print(f"Created {name} group, so creating default permisssions.")
            assert to_add
            group.permissions.set(to_add)


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    def ready(self):
        from auditlog.registry import auditlog
        from rest_framework.authtoken.models import Token

        import web.signals  # noqa: F401

        auditlog.register(Token)

        def new_str(self):
            return self.key[:3] + "." * 10

        # Ensure that the audit log does not log the token key.
        Token.__str__ = new_str

        # Ensure that groups are setup correctly.
        post_migrate.connect(setup_groups, sender=self)
