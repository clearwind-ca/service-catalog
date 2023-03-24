from django.apps import apps
from django.contrib import messages
from django.contrib.messages import constants
from django.db import models


class SystemLog(models.Model):
    target_app_label = models.CharField(max_length=255)
    target_model_name = models.CharField(max_length=255)
    target_slug = models.CharField(max_length=255)
    level = models.IntegerField(
        choices=[(k, v) for k, v in constants.DEFAULT_LEVELS.items()]
    )
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def get_target(self):
        return apps.get_model(
            self.target_app_label, self.target_model_name
        ).objects.get(slug=self.target_slug)


def get_target_filters(target):
    return {
        "target_app_label": target._meta.app_label,
        "target_model_name": target._meta.model_name,
        "target_slug": target.slug,
    }


def get_logs(target):
    return SystemLog.objects.filter(**get_target_filters(target)).order_by("-created")


def add_log(target, level, message, add_message=False, request=None, **kwargs):
    if add_message:
        assert request, "Request is required if add_message is True"
        messages.add_message(request, level, message)

    kwargs = get_target_filters(target)
    kwargs.update(
        {
            "level": level,
            "message": message,
        }
    )
    return SystemLog.objects.create(**kwargs)
