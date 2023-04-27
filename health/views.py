from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalog.errors import NoRepository, SendError
from gh import send
from services.models import Service
from web.helpers import process_query_params

from .forms import CheckForm
from .models import RESULT_CHOICES, STATUS_CHOICES, Check, CheckResult
from .serializers import CheckResultSerializer, CheckSerializer


@login_required
@process_query_params
def checks(request):
    filters = {}
    get = request.GET
    for param, lookup in (("active", "active"),):
        if get.get(param) is not None:
            filters[lookup] = get[param]

    checks = Check.objects.filter(**filters).order_by("-created")

    paginator = Paginator(checks, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "checks": page_obj,
        "filters": filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "active": ["yes", "no"],
    }
    return render(request, "checks-list.html", context)


@login_required
def checks_add(request):
    if request.method == "POST":
        form = CheckForm(request.POST)
        if form.is_valid():
            check = form.save()
            messages.info(request, f"Added health check `{check.name}`")
            return redirect(reverse("health:checks-list"))
    else:
        form = CheckForm()

    return render(
        request, "checks-add.html", {"form": form, "repo": settings.GITHUB_CHECK_REPOSITORY}
    )


@login_required
def checks_detail(request, slug):
    check = Check.objects.get(slug=slug)
    log = LogEntry.objects.get_for_object(check).order_by("-timestamp").first()
    return render(request, "checks-detail.html", {"check": check, "log": log})


@login_required
def checks_update(request, slug):
    check = Check.objects.get(slug=slug)
    if request.method == "POST":
        form = CheckForm(request.POST, instance=check)
        if form.is_valid():
            check = form.save()
            messages.info(request, f"Updated health check `{check.name}`")
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-update.html", {"check": check, "form": form})

    form = CheckForm(instance=check)
    return render(request, "checks-update.html", {"check": check, "form": form})


@login_required
@require_POST
def checks_delete(request, slug):
    Check.objects.get(slug=slug).delete()
    messages.info(request, f"Health check `{slug}` and matching results deleted")
    return redirect(reverse("health:checks-list"))


def adhoc_run(request, check):
    service_queryset = Service.objects.all()
    for service in service_queryset:
        result = CheckResult.objects.create(
            health_check=check,
            status="sent",
            service=service,
        )
        try:
            # Should this use the cron user?
            send.dispatch(request.user, result)
        except (SendError, NoRepository) as error:
            # Fatal error, they are all going to fail.
            # Should we log here?
            result.status = "error"
            result.save()
            raise error


@login_required
@require_POST
def checks_run(request, slug):
    check = Check.objects.get(slug=slug)
    try:
        adhoc_run(request, check)
    except (SendError, NoRepository) as error:
        messages.error(request, f"Failed to send health check: `{error.message}`")
        return redirect(reverse("health:checks-detail", kwargs={"slug": slug}))

    messages.info(request, f"Health check `{slug}` run for all services.")
    return redirect(reverse("health:checks-detail", kwargs={"slug": slug}))


@api_view(["POST"])
def api_checks_run(request, pk):
    check = Check.objects.get(pk=pk)
    try:
        adhoc_run(request, check)
    except (SendError, NoRepository) as error:
        return Response({"success": False}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({"success": True})


@login_required
@process_query_params
def results(request):
    filters, display_filters = {}, {}
    get = request.GET
    for param, lookup in (
        ("result", "result"),
        ("status", "status"),
        ("service", "service__slug"),
        ("check", "health_check__slug"),
    ):
        if get.get(param) is not None:
            filters[lookup] = get[param]
            display_filters[param] = get[param]

    results = CheckResult.objects.filter(**filters).order_by("-created")

    paginator = Paginator(results, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "results": page_obj,
        "filters": display_filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "result_choices": dict(RESULT_CHOICES).keys(),
        "status_choices": dict(STATUS_CHOICES).keys(),
    }
    return render(request, "results-list.html", context)


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all().order_by("-created")
    serializer_class = CheckSerializer
    permission_classes = [permissions.IsAuthenticated]


class CheckResultViewSet(viewsets.ModelViewSet):
    queryset = CheckResult.objects.all().order_by("-created")
    serializer_class = CheckResultSerializer
    permission_classes = [permissions.IsAuthenticated]
