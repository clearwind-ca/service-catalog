from django.conf import settings
from django.core.paginator import Paginator

default_query_params = {"per_page": 10, "page": 1, "active": True}
YES_NO_CHOICES = (("yes", "True"), ("no", "False"), ("all", None))


def paginate(request, filterset, extra=None):
    queryset = getattr(filterset, "qs", filterset)
    filters = getattr(filterset, "filters", {})
    paginator = Paginator(queryset, per_page=request.GET.get("per_page", 10))
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return {
        "paginator": paginator,
        "page_number": page_number,
        "page": page_obj,
        "page_range": page_obj.paginator.get_elided_page_range(page_number),
        "active": ["yes", "no"],
        "filters": filtered_filters(request.GET, filters, extra=extra),
    }


def filtered_filters(get, filterset, extra=None):
    result = {}
    for _dict in (filterset, get):
        for k in _dict.keys():
            v = get.get(k, None)
            if v:
                result[k] = v
    result.update(extra or {})
    return result


def site_context(request):
    """
    A site wide context processor for adding site wide things.
    """
    groups = request.user.groups.values_list("name", flat=True)
    return {
        # Set to true, and then override in views to False to hide breadcrumbs.
        "breadcrumbs": True,
        "settings": {
            "timezone": settings.TIME_ZONE,
        },
        "member": 'members' in groups,
        "public": "public" in groups,
    }
