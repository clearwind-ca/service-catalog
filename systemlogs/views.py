from django.contrib.auth.decorators import login_required
from django.contrib.messages import constants
from django.core.paginator import Paginator
from django.shortcuts import render
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from web.helpers import process_query_params

from .models import SystemLog

model_map = {
    "service": "services",
    "source": "services",
    "deployment": "deployments",
    "health": "health",
}


@login_required
@process_query_params
def log_list(request):
    get = request.GET
    filters, display_filters = {}, {}
    for param, lookup in (("level", "level"),):
        if get.get(param) is not None:
            filters[lookup] = display_filters[lookup] = get[param]

    if get.get("target") and get.get("slug"):
        target = get["target"]
        _model = apps.get_model(model_name=target, app_label=model_map.get(target))
        _object = _model.objects.get(slug=get["slug"])

        filters["content_type__pk"] = ContentType.objects.get_for_model(_model).pk
        filters["object_id"] = _object.pk

        display_filters['target'] = _object.slug
        display_filters['type'] = target.lower()

    sources = SystemLog.objects.filter(**filters).order_by("-created")
    paginator = Paginator(sources, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "logs": page_obj,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "levels": constants.DEFAULT_LEVELS.values,
        "filters": display_filters,
    }
    return render(request, "log-list.html", context)
