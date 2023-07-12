from collections import Counter
from distutils.util import strtobool

import django_filters
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalog.errors import FileAlreadyExists
from gh import create, fetch
from services.models import Service
from web.helpers import YES_NO_CHOICES, paginate

from .forms import ActionForm, CheckForm
from .models import (
    FREQUENCY_CHOICES,
    RESULT_CHOICES,
    STATUS_CHOICES,
    Check,
    CheckResult,
)
from .serializers import CheckResultSerializer, CheckSerializer
from .tasks import send_to_github


class CheckFilter(django_filters.FilterSet):
    active = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)

    class Meta:
        model = Check
        fields = ["frequency"]


def checks(request):
    if not settings.GITHUB_CHECK_REPOSITORY:
        messages.error(
            request,
            'The "GITHUB_CHECK_REPOSITORY" environment variable is not set. Health Checks will not run.',
        )

    queryset = Check.objects.all().order_by("-created")
    checks = CheckFilter(request.GET, queryset=queryset)
    context = paginate(request, checks)
    context.update(
        {
            "frequency": dict(FREQUENCY_CHOICES).keys(),
            "repo": settings.GITHUB_CHECK_REPOSITORY,
        }
    )
    return render(request, "checks-list.html", context)


@permission_required("health.add_check")
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


@permission_required("health.add_check")
def checks_add_action(request, slug):
    check = get_object_or_404(slug=slug, klass=Check)
    nwo = fetch.url_to_nwo(settings.GITHUB_CHECK_REPOSITORY)
    if request.POST:
        form = ActionForm(request.POST)
        if form.is_valid():
            try:
                action = create.create_action_file(*nwo, form.cleaned_data, check)
            except FileAlreadyExists as error:
                messages.error(request, error.message)
            else:
                messages.info(request, f"Added action file `{action.html_url}`")
                return redirect(reverse("health:checks-list"))

    else:
        form = ActionForm()

    return render(
        request,
        "checks-add-action.html",
        {"form": form, "check": check, "repo": settings.GITHUB_CHECK_REPOSITORY},
    )


def checks_detail(request, slug):
    check = get_object_or_404(slug=slug, klass=Check)
    log = LogEntry.objects.get_for_object(check).order_by("-timestamp").first()
    results = (
        CheckResult.objects.filter(health_check=check)
        .order_by("service", "-updated")
        .distinct("service")
    )
    result = results.first()
    results_data = dict(Counter(results.values_list("result", flat=True)))
    results_total = sum(results_data.values())
    return render(
        request,
        "checks-detail.html",
        {
            "check": check,
            "log": log,
            "result": result,
            "results_data": results_data,
            "results_total": results_total,
        },
    )


@permission_required("health.change_check")
def checks_update(request, slug):
    check = get_object_or_404(slug=slug, klass=Check)
    if request.method == "POST":
        form = CheckForm(request.POST, instance=check)
        if form.is_valid():
            check = form.save()
            messages.info(request, f"Updated health check `{check.name}`")
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-update.html", {"check": check, "form": form})

    form = CheckForm(instance=check)
    return render(request, "checks-update.html", {"check": check, "form": form})


@require_POST
@permission_required("health.delete_check")
def checks_delete(request, slug):
    get_object_or_404(Check, slug=slug).delete()
    messages.info(request, f"Health check `{slug}` and matching results deleted")
    return redirect(reverse("health:checks-list"))


def send(check):
    service_queryset = Service.objects.filter(active=True)
    for service in service_queryset:
        send_to_github.delay(check.slug, service.slug)


# Sending a check is essentially asking something to change it
# so let's use the same permissions here.
@require_POST
@permission_required("health.change_check")
def checks_run(request, slug):
    check = get_object_or_404(Check, slug=slug)
    send(check)
    messages.info(request, f"Health check `{slug}` queued for all services.")
    return redirect(reverse("health:checks-detail", kwargs={"slug": slug}))


@api_view(["POST"])
@permission_required("health.change_check")
def api_checks_run(request, pk):
    check = get_object_or_404(Check, pk=pk)
    send(request.user.username, check)
    return Response({"success": True})


class CheckResultFilter(django_filters.FilterSet):
    class Meta:
        model = CheckResult
        fields = ["result", "status", "service__slug", "health_check__slug"]


def results(request):
    queryset = CheckResult.objects.all().order_by("-created")
    results = CheckResultFilter(request.GET, queryset=queryset)
    context = paginate(request, results)
    context.update(
        {
            "result_choices": dict(RESULT_CHOICES).keys(),
            "status_choices": dict(STATUS_CHOICES).keys(),
        }
    )
    return render(request, "results-list.html", context)


def results_detail(request, pk):
    result = get_object_or_404(CheckResult, pk=pk)
    log = LogEntry.objects.get_for_object(result).order_by("-timestamp").first()
    return render(request, "results-detail.html", {"result": result, "log": log})


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all().order_by("-created")
    serializer_class = CheckSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class CheckResultViewSet(viewsets.ModelViewSet):
    queryset = CheckResult.objects.all().order_by("-created")
    serializer_class = CheckResultSerializer
    permission_classes = [permissions.DjangoModelPermissions]
