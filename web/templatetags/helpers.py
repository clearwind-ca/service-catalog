import zoneinfo
from urllib.parse import urlencode

import markdown
from django import template
from django.urls import reverse
from django.utils.html import urlize
from django.utils.safestring import mark_safe

from web.helpers import default_query_params

register = template.Library()

import json


@register.filter(name="priority_as_colour")
def priority_as_colour(value):
    levels = {
        1: "primary",
        2: "primary",
        3: "primary",
        4: "secondary",
        5: "secondary",
    }
    return levels.get(value, "dark")


@register.filter(name="check_as_colour")
def check_as_colour(value):
    result = {
        "pass": "success",
        "warning": "warning",
        "error": "danger",
        "unknown": "secondary",
        "fail": "danger",
    }
    return result.get(value, "dark")


@register.filter(name="status_as_colour")
def status_as_colour(value):
    result = {
        "sent": "secondary",
        "error": "danger",
        "timed-out": "warning",
        "completed": "success",
    }
    return result.get(value, "dark")


@register.filter(name="markdown")
def markdown_filter(text):
    md = markdown.Markdown(safe_mode=True, extensions=["extra", "mdx_linkify"])
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
        if check["last"].result != "pass":
            all_passing = False
            break

    if not_run:
        result["colour"] = "secondary"
        result["text"] = "No health checks run"
    elif all_passing:
        result["text"] = "All health checks pass"
        result["colour"] = "success"
    else:
        result["colour"] = "warning"
        result["text"] = "Some checks failing"

    return result


@register.filter(name="dict_key")
def dict_key(d, k):
    return d.get(k)


@register.filter(name="choice_value")
def choice_value(v):
    if isinstance(v, (list, tuple)):
        return v[1]
    return v


@register.simple_tag(name="get_as_css")
def get_as_css(request, key, value):
    if request.GET.get(key) == value:
        return "active"
    return ""


@register.simple_tag(name="qs")
def qs(request, override_key, override_value):
    """
    A tag that generates a query string based on the current request.
    """

    def convert(v):
        if isinstance(v, bool) and v in [True, False]:
            return "yes" if v else "no"
        return v

    qs = {}
    for k in request.GET.keys():
        v = request.GET.get(k)
        if v is not None:
            qs[k] = convert(v)

    if not override_value and override_key in qs:
        del qs[override_key]
    elif override_value:
        qs[override_key] = convert(override_value)

    # Since this is the default, no point in passing it around.
    for k, v in default_query_params.items():
        if v is not None and k in qs:
            if qs[k] == v:
                del qs[k]
    return "?" + urlencode(qs) if qs else "?"


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


@register.filter
def yesno_if_boolean(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    return value
