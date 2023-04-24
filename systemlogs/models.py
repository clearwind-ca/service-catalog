from django.contrib import messages


def add_log(*args, **kwargs):
    raise NotImplementedError


def add_info(request, message):
    return messages.add_message(request, messages.INFO, message)


def add_error(request, message):
    return messages.add_message(request, messages.ERROR, message)
