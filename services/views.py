from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from catalog.errors import FetchError
from gh import fetch
from systemlogs.models import SystemLog, add_log, get_target_filters
from web.helpers import process_query_params

from .forms import ServiceForm, SourceForm, get_schema
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
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
    }
    return render(request, "service-list.html", context)


@login_required
@require_POST
def service_delete(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    service.delete()
    add_log(
        service,
        messages.INFO,
        "Service successfully deleted",
        add_message=True,
        request=request,
    )
    return redirect("services:service_list")


@login_required
def service_detail(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    context = {
        "service": service,
        "source": service.source,
        "logs": SystemLog.objects.filter(**get_target_filters(service)).order_by(
            "-created"
        )[:3],
    }
    return render(request, "service-detail.html", context)


@login_required
@process_query_params
def source_list(request):
    sources = Source.objects.filter().order_by("url")
    get = request.GET

    paginator = Paginator(sources, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "sources": page_obj,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
    }
    return render(request, "source-list.html", context)


@login_required
def source_detail(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    context = {
        "services": source.services.all(),
        "source": source,
        "logs": SystemLog.objects.filter(**get_target_filters(source)).order_by(
            "-created"
        )[:3],
    }
    return render(request, "source-detail.html", context)


def _create_service(data, source):
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
            try:
                dependency = Service.objects.get(slug=dependency)
            except ObjectDoesNotExist:
                add_log(
                    service,
                    messages.WARNING,
                    "Dependency `{}` skipped because it does not exist when processing the catalog data".format(
                        dependency
                    ),
                )
                continue
            service.dependencies.add(dependency)

    return service


def _update_service(data, slug):
    service = Service.objects.get(slug=slug)
    service.name = data["name"]
    service.description = data.get("description")
    service.type = data["type"]
    service.level = data["level"]
    service.meta = data.get("meta")
    service.save()

    # Add in dependencies if they exist, otherwise log a message.
    if "dependencies" in data:
        for dependency in data["dependencies"]:
            try:
                dependency = Service.objects.get(slug=dependency)
            except ObjectDoesNotExist:
                add_log(
                    service,
                    messages.WARNING,
                    "Dependency `{}` skipped because it does not exist when processing the catalog data".format(
                        dependency
                    ),
                )
                continue
            service.dependencies.add(dependency)

    # Remove any depenedencies that are not in the catalog data.
    for dependency in service.dependencies.all():
        if dependency.slug not in data["dependencies"]:
            add_log(
                service,
                messages.INFO,
                "Removed dependency {} because it is not in the catalog data".format(
                    dependency
                ),
            )
            service.dependencies.remove(dependency)

    return service


def _refresh_source(data, source):
    slug = slugify(data["name"])
    exists = Service.objects.filter(slug=slug).exists()
    if not exists:
        service = _create_service(data, source)
        msg = f"Created service `{service.slug}` successfully."
    else:
        service = _update_service(data, slug)
        msg = f"Refreshed service `{service.slug}` successfully."
    return (service, msg)


@login_required
@process_query_params
def source_refresh(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        results = fetch.get(request.user, source)
    except FetchError as error:
        add_log(
            source, messages.ERROR, error.message, add_message=True, request=request
        )
        return redirect("services:source_detail", slug=source.slug)

    for data in results:
        service, msg = _refresh_source(data["contents"], source)
        add_log(service, messages.INFO, msg, add_message=True, request=request)
    return redirect("services:source_detail", slug=source.slug)


@login_required
def source_add(request):
    if request.method == "GET":
        return render(
            request, "source-add.html", context={"file_paths": fetch.file_paths}
        )
    else:
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save()
            add_log(
                source,
                messages.INFO,
                "Source successfully added",
                add_message=True,
                request=request,
            )
            try:
                data = fetch.get(request.user, source)
            except FetchError as error:
                messages.add_message(request, messages.ERROR, error.message)
                return redirect("services:source_list")

            service, msg = _refresh_source(data, source)
            add_log(service, messages.INFO, msg, add_message=True, request=request)
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
    add_log(
        source,
        messages.INFO,
        "Source successfully deleted",
        add_message=True,
        request=request,
    )
    return redirect("services:source_list")


@login_required
def source_validate(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        data = fetch.get(request.user, source)
    except (FetchError) as error:
        add_log(
            source, messages.ERROR, error.message, add_message=True, request=request
        )
        return redirect("services:source_detail", slug=source.slug)

    form = ServiceForm({"data": data})
    if not form.is_valid():
        message = f"Validation failed for: `{source.url}`."
        add_log(source, messages.ERROR, message, add_message=True, request=request)
        return redirect("services:source_detail", slug=source.slug)

    add_log(
        source,
        messages.INFO,
        "Source successfully validated",
        add_message=True,
        request=request,
    )
    return redirect("services:source_detail", slug=source.slug)


@login_required
def schema_detail(request):
    return render(
        request,
        "schema-detail.html",
        {"path": settings.SERVICE_SCHEMA, "schema": get_schema()},
    )
