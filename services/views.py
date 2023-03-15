from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from jsonschema import ValidationError

from catalog.errors import FetchError
from gh import fetch
from web.helpers import process_query_params

from .forms import SourceForm
from .models import Service, Source


@login_required
@process_query_params
def service_list(request):
    filters = {}
    get = request.GET
    for param, lookup in (
        ("active", "active"),
        ("level", "level"),
        ("source", "source__slug"),
    ):
        if get.get(param) is not None:
            filters[lookup] = get[param]

    services = Service.objects.filter(**filters).order_by("name")

    paginator = Paginator(services, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "services": page_obj,
        "levels": sorted(
            [k[0] for k in Service.objects.values_list("level").distinct()]
        ),
        "filters": filters,
    }
    return render(request, "service-list.html", context)


@require_POST
@login_required
def service_delete(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    service.delete()
    messages.add_message(request, messages.INFO, "Service successfully deleted")
    return redirect("services:service_list")


@login_required
def service_detail(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    context = {"service": service, "source": service.source}
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
    try:
        data = fetch.get(request.user, source)
    except FetchError as error:
        messages.add_message(request, messages.ERROR, error.message)
        return redirect("services:source_list")

    slug = slugify(data["name"])
    exists = Service.objects.filter(slug=slug).exists()
    if not exists:
        service = Service.objects.create(
            name=data["name"],
            description=data.get("description"),
            type=data["type"],
            level=data["level"],
            meta=data.get("meta"),
            source=source,
        )
        if "dependencies" in data:
            for dependency in data["dependencies"]:
                dependency = Service.objects.get(slug=dependency)
                service.dependencies.add(dependency)
        messages.add_message(request, messages.INFO, "Created service successfully")
    else:
        service = Service.objects.get(slug=slug)
        service.name = data["name"]
        service.description = data.get("description")
        service.type = data["type"]
        service.level = data["level"]
        service.meta = data.get("meta")
        service.save()
        if "dependencies" in data:
            for dependency in data["dependencies"]:
                print(dependency)
                dependency = Service.objects.get(slug=dependency)
                service.dependencies.add(dependency)
        messages.add_message(
            request,
            messages.INFO,
            "Refreshed service successfully",
        )
    return redirect("services:service_detail", slug=service.slug)


@login_required
def source_add(request):
    if request.method == "GET":
        return render(request, "source-add.html")
    else:
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, "Source successfully added")
            return redirect("services:source_list")
        else:
            messages.add_message(request, messages.ERROR, form.nice_errors())
            return render(request, "source-add.html")


@login_required
@require_POST
def source_delete(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    if source.services.exists():
        messages.add_message(
            request,
            messages.ERROR,
            "Source cannot be deleted because it is associated with at least one service. Delete the services first.",
        )
        return redirect("services:source_list")
    source.delete()
    messages.add_message(request, messages.INFO, "Source successfully deleted")
    return redirect("services:source_list")


@login_required
def source_validate(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        data = fetch.validate(request.user, source)
    except (ValidationError, FetchError) as error:
        msg = "Source failed validation: {}".format(error.message)
        messages.add_message(request, messages.ERROR, msg)
        return redirect("services:source_list")

    messages.add_message(request, messages.INFO, "Source successfully validated")
    return redirect("services:source_list")


@login_required
def schema_detail(request):
    return render(
        request,
        "schema-detail.html",
        {"path": settings.SERVICE_SCHEMA, "schema": fetch.get_schema()},
    )
