def attempt_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        pass


def attempt_yesno(value):
    if value is None:
        return
    try:
        value = str(value).lower()
    except (TypeError, ValueError):
        pass
    return {
        "yes": True,
        "no": False,
    }.get(value)


default_query_params = {
    "per_page": 10,
    "page": None,
    "active": None,
    "level": None,
    "source": None,
}


def process_query_params(func):
    """
    A decorator for processing query params, that we'll use in any list view.
    """

    def wrapper(request, *args, **kwargs):
        parsed = default_query_params.copy()
        parsed["page"] = attempt_int(request.GET.get("page", 1)) or 1
        parsed["active"] = attempt_yesno(request.GET.get("active"))
        parsed["level"] = attempt_int(request.GET.get("level"))
        parsed["source"] = request.GET.get("source")

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
        "breadcrumbs": True
    }
