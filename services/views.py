from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import CharField, Value
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.errors import FetchError, SchemaError
from gh import fetch
from systemlogs.models import add_error, add_info
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
        ("priority", "priority"),
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
        "priorities": sorted(
            [k[0] for k in Service.objects.values_list("priority").distinct()]
        ),
        "filters": filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
    }
    return render(request, "service-list.html", context)


@login_required
@require_POST
def service_delete(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    msg = f"Service `{service.slug}` successfully deleted"
    add_info(service, msg, web=True, request=request)
    service.delete()
    return redirect("services:service_list")


@login_required
def service_detail(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    context = {
        "service": service,
        "source": service.source,
        "related": list(
            chain(
                service.dependencies.annotate(
                    relation=Value("dependency", output_field=CharField())
                ),
                service.dependents().annotate(
                    relation=Value("dependent", output_field=CharField())
                ),
            )
        ),
        "logs": service.logs().order_by("-created")[:3],
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
        "logs": source.logs().order_by("-created")[:3],
    }
    return render(request, "source-detail.html", context)


@login_required
@process_query_params
def source_refresh(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        results = fetch.get(request.user, source)
    except FetchError as error:
        msg = f"Error refreshing `{source.slug}`: {error.message}"
        add_error(source, msg, web=True, request=request)
        return redirect("services:source_detail", slug=source.slug)

    refresh_results(results, source, request)
    return redirect("services:source_detail", slug=source.slug)


def refresh_results(results, source, request):
    """
    A helper that takes the list of results from gh fetch and runs
    them through the service form, logging any output.
    """
    for data in results:
        form = ServiceForm({"data": data["contents"]})
        form.source = source
        if form.is_valid():
            result = form.save()
            for log in result["logs"]:
                msg = f"Refreshed `{source.slug}` successfully."
                add_info(result["service"], msg, web=True, request=request)

        else:
            msg = f"Refresh error on `{source.slug}`: {form.nice_errors()}."
            add_error(source, msg, web=True, request=request)


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
            try:
                results = fetch.get(request.user, source)
            except FetchError as error:
                messages.add_message(request, messages.ERROR, error.message)
                return redirect("services:source_list")

            refresh_results(results, source, request)
        else:
            messages.add_message(request, messages.ERROR, form.nice_errors())

        return render(request, "source-add.html")


@login_required
@require_POST
def source_delete(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    if source.services.exists():
        err = "Source cannot be deleted because it is associated with at least one service. Delete the services first."
        messages.add_message(request, messages.ERROR, err)
        return redirect("services:source_list")

    add_info(
        source,
        f"Source {source.slug} successfully deleted",
        web=True,
        request=request,
    )
    source.delete()
    return redirect("services:source_list")


@login_required
def source_validate(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        results = fetch.get(request.user, source)
    except (FetchError) as error:
        add_error(source, error.message, web=True, request=request)
        return redirect("services:source_detail", slug=source.slug)

    for data in results:
        form = ServiceForm({"data": data["contents"]})
        if not form.is_valid():
            message = f"Validation failed for: `{source.url}`. Error: {form.nice_errors()}."
            add_error(source, message, web=True, request=request)
            return redirect("services:source_detail", slug=source.slug)

    add_info(
        source,
        f"Source `{source.slug}` successfully validated.",
        web=True,
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
