from urllib.parse import urlencode

import markdown
from django import template
from django.contrib.messages import constants
from django.urls import reverse
from django.utils.html import urlize
from django.utils.safestring import mark_safe

from web.helpers import default_query_params

register = template.Library()

import json


@register.filter(name="priority_as_colour")
def priority_as_colour(value):
    levels = {
        1: "warning",
        2: "primary",
        3: "primary",
        4: "secondary",
        5: "secondary",
    }
    return levels.get(value, "dark")


@register.filter(name="log_level_as_colour")
def log_level_as_colour(value):
    levels = {
        10: "secondary",
        20: "secondary",
        25: "primary",
        30: "warning",
        40: "danger",
    }
    return levels.get(value, "dark")


@register.filter(name="log_level_as_text")
def log_level_as_text(value):
    levels = {
        constants.DEBUG: "Debug",
        constants.INFO: "Info",
        constants.SUCCESS: "Success",
        constants.WARNING: "Warning",
        constants.ERROR: "Error",
    }
    return levels.get(value, "Unknown")


@register.filter(name="check_as_colour")
def check_as_colour(value):
    result = {
        "pass": "success",
        "warning": "warning",
        "error": "danger",
        "unconfirmed": "secondary",
        "fail": "danger",
    }
    return result.get(value, "dark")


@register.filter(name="status_as_colour")
def status_as_colour(value):
    result = {"S": "secondary", "R": "success", "F": "danger"}
    return result.get(value, "dark")


@register.filter(name="markdown")
def markdown_filter(text):
    md = markdown.Markdown()
    return mark_safe(md.convert(text))


@register.simple_tag(name="checks_badge")
def checks_badge(checks):
    result = {
        "colour": "dark",
        "text": "No health checks run",
    }

    not_run = True
    all_passing = True
    for check in checks:
        if check["last"] is None:
            all_passing = False
            continue
        not_run = False
        if check["last"].result != "P":
            all_passing = False
            break

    if all_passing:
        result["text"] = "All health checks pass"
        result["colour"] = "success"
    elif not_run:
        result["colour"] = "info"
        result["text"] = "No health checks run"
    else:
        result["colour"] = "warning"
        result["text"] = "Some checks failing"

    return result


@register.simple_tag(name="qs")
def qs(request, **overrides):
    """
    A tag that generates a query string based on the current request.

    It assumes that the template that uses this, is from a view that has
    the `process_query_params` decorator applied to it. Because that
    decorator will format all these query params the right way.
    """

    def convert(v):
        if isinstance(v, bool) and v in [True, False]:
            return "yes" if v else "no"
        return v

    qs = {}
    for k in default_query_params.keys():
        v = request.GET.get(k)
        if v is not None:
            qs[k] = convert(v)

    for k, v in overrides.items():
        if not v and k in qs:
            del qs[k]
        elif v:
            qs[k] = convert(v)

    # Since this is the default, no point in passing it around.
    for k, v in default_query_params.items():
        if v is not None:
            if qs[k] == v:
                del qs[k]

    return "?" + urlencode(qs) if qs else "?"


valid_formats = ("url", "md")


@register.filter(name="strip")
def strip_format(value):
    if value.endswith(valid_formats):
        value = value.rsplit("_", 1)[0]
    return value.replace("_", " ").replace("-", " ").title()


@register.simple_tag(name="apply")
def apply_format(value, field):
    _format = None
    if field in valid_formats:
        _format = value

    possible_format = field.rsplit("_", 1)[-1]
    if possible_format in valid_formats:
        _format = possible_format

    if not _format:
        return value

    if _format == "url":
        return mark_safe(urlize(value))

    if _format == "md":
        return markdown_filter(value)


@register.simple_tag(name="at_url")
def at_url(request, url):
    """A simple tag to detect if the user is at a certain url, useful for navigation"""
    try:
        if request.path.startswith(reverse(url)):
            return "active"
    except AttributeError:
        return ""
    return ""


@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4)
