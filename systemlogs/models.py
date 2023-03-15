from django.apps import apps
from django.contrib.messages import constants as messages
from django.db import models


class SystemLog(models.Model):
    target_app_label = models.CharField(max_length=255)
    target_model_name = models.CharField(max_length=255)
    target_slug = models.CharField(max_length=255)
    level = models.IntegerField(
        choices=[(k, v) for k, v in messages.DEFAULT_LEVELS.items()]
    )
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def get_target(self):
        return apps.get_model(
            self.target_app_label, self.target_model_name
        ).objects.get(slug=self.target_slug)


def add(target, level, message, **kwargs):
    return SystemLog.objects.create(
        target_app_label=target._meta.app_label,
        target_model_name=target._meta.model_name,
        target_slug=target.slug,
        level=level,
        message=message,
    )
