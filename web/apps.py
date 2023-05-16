from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    def ready(self):
        from auditlog.registry import auditlog
        from django.contrib.auth.models import User

        import web.signals  # noqa: F401

        auditlog.register(User)

        from rest_framework.authtoken.models import Token

        auditlog.register(Token)

        def new_str(self):
            return self.key[:3] + "." * 10

        # Ensure that the audit log does not log the token key.
        Token.__str__ = new_str
