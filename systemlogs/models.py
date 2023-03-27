from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import constants
from django.db import models


class SystemLog(models.Model):
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)

    level = models.IntegerField(
        choices=[(k, v) for k, v in constants.DEFAULT_LEVELS.items()]
    )
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )


def add_log(target, level, message, add_message=False, request=None, **kwargs):
    """
    Add a log into the system log

    :param target: The target object
    :param level: The level of the log, using the constants from django.contrib.messages
    :param message: The message to log, markdown accepted.
    :param add_message: Whether to add the message to the request messages and show in the browser.
    :param request: The request object, required if add_message is True. Will add in the user who made the change.
    """
    if add_message:
        assert request, "Request is required if add_message is True"
        messages.add_message(request, level, message)

    kwargs.update(
        {
            "content_object": target,
            "level": level,
            "message": message,
            "user": request.user if request else None,
        }
    )
    entry = SystemLog.objects.create(**kwargs)
    entry.save()
    return entry
