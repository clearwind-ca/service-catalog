from django.contrib.auth.decorators import login_required
from django.contrib.messages import constants
from django.core.paginator import Paginator
from django.shortcuts import render

from web.helpers import process_query_params

from .models import SystemLog


@login_required
@process_query_params
def log_list(request):
    get = request.GET
    filters = {}
    for param, lookup in (
        ("level", "level"),
        ("target", "target_model_name"),
        ("slug", "target_slug"),
    ):
        if get.get(param) is not None:
            filters[lookup] = get[param]

    sources = SystemLog.objects.filter(**filters).order_by("-created")
    paginator = Paginator(sources, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "logs": page_obj,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "levels": constants.DEFAULT_LEVELS.values,
        "filters": filters,
    }
    return render(request, "log-list.html", context)
