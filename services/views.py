from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from web.helpers import process_query_params

from .models import Service


@login_required
@process_query_params
def list(request):
    filters = {}
    get = request.GET
    for (param, field) in [("active", "is_active"), ("level", "service_level")]:
        if get[param] is not None:
            filters[field] = get[param]

    services = Service.objects.filter(**filters).order_by("name")
    if not services:
        services_exist = bool(Service.objects.count())

    paginator = Paginator(services, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "services": page_obj,
        "levels": sorted(
            [k[0] for k in Service.objects.values_list("service_level").distinct()]
        ),
    }
    return render(request, "list.html", context)


@login_required
def show(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    context = {
        "service": service,
    }
    return render(request, "show.html", context)
