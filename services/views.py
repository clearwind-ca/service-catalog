import json
from distutils.util import strtobool
from itertools import chain

import django_filters
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import connection
from django.db.models import CharField, Value
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from catalog.errors import FetchError, FileAlreadyExists
from events.models import Event
from gh import create, fetch
from web.helpers import YES_NO_CHOICES, paginate

from .forms import OrgForm, ServiceForm, SourceForm, get_schema
from .models import Organization, Service, Source
from .serializers import ServiceSerializer, SourceSerializer
from .tasks import refresh_orgs_from_github


class ServiceFilter(django_filters.FilterSet):
    active = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)

    class Meta:
        model = Service
        fields = ["priority", "source__slug"]


def service_list(request):
    queryset = Service.objects.all().order_by("priority", "name")
    services = ServiceFilter(request.GET, queryset=queryset)
    context = paginate(request, services)
    context.update(
        {
            "priorities": [str(k) for k in range(1, 11)],
        }
    )
    return render(request, "service-list.html", context)


def service_tree(request, slug):
    # Start with a simple naive tree that won't scale.
    sql = """
WITH RECURSIVE ctename AS (
        SELECT id, CAST(0 AS BIGINT) AS parent, 0 AS level
        FROM services_service
        WHERE id = %s
    UNION ALL
        SELECT to_service_id, from_service_id, ctename.level + 1
        FROM services_service_dependencies
        JOIN ctename ON services_service_dependencies.from_service_id = ctename.id
    )
SELECT id, parent, level FROM ctename WHERE level <= 10 ORDER BY level ASC;
"""
    root = get_object_or_404(slug=slug, klass=Service)
    tree = Service.objects.raw(sql, [root.pk])

    context = {
        "tree": tree,
        "service": root,
        "dependencies": root.dependents(),
    }
    return render(request, "tree.html", context)


@require_POST
@permission_required("services.delete_service")
def service_delete(request, slug):
    service = get_object_or_404(slug=slug, klass=Service)
    messages.info(request, f"Service `{service.slug}` successfully deleted")
    service.delete()
    return redirect("services:service-list")


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
        "checks": service.latest_results(),
        "log": LogEntry.objects.get_for_object(service).order_by("-timestamp").first(),
        "events": Event.objects.filter(services__in=[service], start__gt=timezone.now()).order_by(
            "start"
        )[:3],
        "pk": service.pk,
        "type": "service",
    }
    return render(request, "service-detail.html", context)


def source_list(request):
    queryset = Source.objects.filter().order_by("url")
    context = paginate(request, queryset)
    context.update(
        {
            "orgs": Organization.objects.all(),
        }
    )
    return render(request, "source-list.html", context)


def source_detail(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    context = {
        "services": source.services.all(),
        "source": source,
        "log": LogEntry.objects.get_for_object(source).order_by("-timestamp").first(),
    }
    return render(request, "source-detail.html", context)


@permission_required("services.change_source")
def source_refresh(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        results = fetch.get(source)
    except FetchError as error:
        msg = f"Error attempting to refresh: `{source.slug}` via the web. {error.message}"
        messages.error(request, msg)
        return redirect("services:source-detail", slug=source.slug)

    refresh_results(results, source, request)
    return redirect("services:source-detail", slug=source.slug)


@require_POST
@permission_required("services.change_source")
def org_refresh(request):
    refresh_orgs_from_github.delay()
    messages.info(request, "Refresh of data from GitHub successfully queued.")
    return redirect("services:source-list")


@api_view(["POST"])
@permission_required("services.change_source")
def api_source_refresh(request, pk):
    source = get_object_or_404(pk=pk, klass=Source)
    try:
        results = fetch.get(source)
    except FetchError as error:
        msg = f"Error attempting to refresh: `{source.slug}` via the api. {error.message}"
        messages.error(request, msg)
        return Response({"success": False}, status=status.HTTP_502_BAD_GATEWAY)

    refresh_results(results, source, request)
    return Response({"success": True})


def refresh_results(results, source, request):
    """
    A helper that takes the list of results from gh fetch and runs
    them through the service form, logging any output.

    Should we do this in background? Maybe, but it gives direct feedback to the user, so going to leave it for now.
    """
    for data in results:
        form = ServiceForm({"data": data["contents"]})
        form.source = source
        if form.is_valid():
            form.save()
            source.updated = timezone.now()
            source.save()
        else:
            messages.error(request, f"Refresh error on `{source.slug}`: {form.nice_errors()}.")
            break

    messages.info(request, f"Refreshed source `{source.slug}` successfully.")


@permission_required("services.add_source")
def source_add(request):
    if request.method == "GET":
        return render(
            request,
            "source-add.html",
            context={"file_paths": fetch.file_paths, "form": SourceForm()},
        )
    else:
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save()
            try:
                results = fetch.get(source)
            except FetchError as error:
                messages.error(request, error.message)
                return redirect("services:source-list")

            refresh_results(results, source, request)
        else:
            messages.error(request, form.nice_errors())

    return redirect("services:source-list")


@require_POST
@permission_required("services.delete_source")
def source_delete(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    if source.services.exists():
        err = f"Source `{source.slug}` cannot be deleted because it is associated with at least one service. Delete the services first."
        messages.add_message(request, messages.ERROR, err)
        return redirect("services:source-list")

    messages.info(request, f"Source `{source.slug}` successfully deleted")
    source.delete()
    return redirect("services:source-list")


@permission_required("services.change_source")
def source_update(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    if request.POST:
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            source = form.save()
            messages.info(request, f"Source `{source.slug}` successfully updated")
            return redirect("services:source-detail", slug=source.slug)
    else:
        form = SourceForm(instance=source)

    return render(request, "source-update.html", context={"form": form, "source": source})


@permission_required("services.change_source")
def source_validate(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    try:
        results = fetch.get(source)
    except (FetchError) as error:
        messages.error(request, error.message)
        return redirect("services:source-detail", slug=source.slug)

    for data in results:
        form = ServiceForm({"data": data["contents"]})
        if not form.is_valid():
            message = f"Validation failed for: `{source.url}`. Error: {form.nice_errors()}."
            messages.error(request, message)
            return redirect("services:source-detail", slug=source.slug)

    messages.info(request, f"Source `{source.slug}` successfully validated.")
    return redirect("services:source-detail", slug=source.slug)


@api_view(["POST"])
@permission_required("services.change_source")
def api_source_validate(request, pk):
    source = get_object_or_404(pk=pk, klass=Source)
    try:
        results = fetch.get(request.user, source)
    except (FetchError) as error:
        messages.error(request, error.message)
        return Response({"success": False}, status=status.HTTP_502_BAD_GATEWAY)

    response = {"source": SourceSerializer(source).data, "success": False, "failures": []}
    for data in results:
        form = ServiceForm({"data": data["contents"]})
        if not form.is_valid():
            response["failures"].append(json.loads(form.errors.as_json()))

    if not response["failures"]:
        return Response({"success": True})
    else:
        return Response(response, status=status.HTTP_502_BAD_GATEWAY)


@permission_required("services.add_service")
def source_add_service(request, slug):
    source = get_object_or_404(slug=slug, klass=Source)
    nwo = fetch.url_to_nwo(source.url)
    if request.POST:
        try:
            pull = create.create_json_file(*nwo)
        except FileAlreadyExists as error:
            messages.error(request, error.message)
        else:
            messages.info(request, f"Pull request [successfully created]({pull.html_url}).")

    return render(request, "service-add.html", context={"source": source})


def schema_detail(request):
    return render(
        request,
        "schema-detail.html",
        {"path": settings.SERVICE_SCHEMA, "schema": get_schema()},
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def api_schema_detail(request):
    return Response(
        {"path": settings.SERVICE_SCHEMA, "schema": get_schema()},
    )


def org_detail(request, slug):
    org = get_object_or_404(name=slug, klass=Organization)
    if request.method == "POST":
        form = OrgForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect("services:source-list")
        return render(request, "org-detail.html", context={"form": form, "org": org})

    form = OrgForm(instance=org)
    return render(request, "org-detail.html", context={"form": form, "org": org})


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all().order_by("-created")
    serializer_class = SourceSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class ServiceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Service.objects.all().order_by("-created")
    serializer_class = ServiceSerializer
    permission_classes = [permissions.DjangoModelPermissions]
