from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from web.helpers import process_query_params
from django.contrib import messages
from .models import Service, Source
from gh import fetch
from django.utils.text import slugify

@login_required
@process_query_params
def service_list(request):
    filters = {}
    get = request.GET
    for (param, field) in [("active", "is_active"), ("level", "service_level")]:
        if get[param] is not None:
            filters[field] = get[param]

    services = Service.objects.filter(**filters).order_by("name")

    paginator = Paginator(services, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "services": page_obj,
        "levels": sorted(
            [k[0] for k in Service.objects.values_list("service_level").distinct()]
        ),
    }
    return render(request, "service-list.html", context)

@require_POST
@login_required
def service_delete(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    service.delete()
    messages.add_message(request, messages.INFO, "Service successfully deleted",)
    return redirect("services:service_list")

@login_required
def service_detail(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    context = {
        "service": service,
        "source": service.source,
    }
    return render(request, "service-detail.html", context)

@login_required
@process_query_params
def source_list(request):
    sources = Source.objects.filter().order_by("name")
    get = request.GET

    paginator = Paginator(sources, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "sources": page_obj,
    }
    return render(request, "source-list.html", context)

@login_required
@process_query_params
def source_refresh(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    data = fetch.get(request.user, source)
    slug = slugify(data["name"])
    exists = Service.objects.filter(slug=slug).exists()
    if not exists:
        service = Service.objects.create(
            name=data["name"],
            description=data["description"],
            service_type=data["service_type"],
            service_level=data["service_level"],
            ownership=data["ownership"],
            source=source,
        )
        messages.add_message(request, messages.INFO, "Created service successfully")
    else:
        service = Service.objects.get(slug=slug)
        service.name = data["name"]
        service.description = data["description"]
        service.service_type = data["service_type"]
        service.service_level = data["service_level"]
        service.ownership = data["ownership"]
        service.save()
        messages.add_message(request, messages.INFO, "Refreshed service successfully",)
    return redirect("services:service_detail", slug=service.slug)