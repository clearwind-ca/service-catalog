from auditlog.models import LogEntry
from django.conf import settings


def attempt_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        pass


def attempt_yesno(value):
    if value is None:
        return None
    try:
        value = str(value).lower()
    except (TypeError, ValueError):
        pass
    return {
        "yes": True,
        "no": False,
        "all": None,
    }.get(value)


def attempt_yesno_all(value):
    if value is None:
        return default_query_params["active"]
    try:
        value = str(value).lower()
    except (TypeError, ValueError):
        pass
    return {
        "yes": True,
        "no": False,
        "all": None,
    }.get(value)


def attempt_choices(value):
    choices = dict([(v, k) for k, v in LogEntry.Action.choices])
    return choices.get(value, None)


default_query_params = {"per_page": 10, "page": 1, "active": True}


def process_query_params(func):
    """
    A decorator for processing query params, that we'll use in any list view.
    """

    def wrapper(request, *args, **kwargs):
        parsed = default_query_params.copy()
        parsed["page"] = attempt_int(request.GET.get("page", 1)) or 1
        parsed["active"] = attempt_yesno_all(request.GET.get("active"))
        parsed["customers"] = attempt_yesno(request.GET.get("customers"))
        parsed["level"] = attempt_int(request.GET.get("level"))
        parsed["priority"] = attempt_int(request.GET.get("priority"))
        parsed["action"] = attempt_choices(request.GET.get("action"))
        for key in request.GET.keys():
            if key in parsed.keys():
                continue
            parsed[key] = request.GET[key]

        if request.GET.get("per_page"):
            try:
                # Max 100 should be enough.
                parsed["per_page"] = min(int(request.GET["per_page"]), 100)
            except ValueError:
                pass

        request.GET = parsed
        return func(request, *args, **kwargs)

    return wrapper


def site_context(request):
    """
    A site wide context processor for adding site wide things.
    """
    return {
        # Set to true, and then override in views to False to hide breadcrumbs.
        "breadcrumbs": True,
        "settings": {
            "timezone": settings.TIME_ZONE,
        },
    }
