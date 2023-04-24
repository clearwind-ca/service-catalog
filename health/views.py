from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from systemlogs.models import add_info
from web.helpers import process_query_params

from .forms import CheckForm
from .models import RESULT_CHOICES, STATUS_CHOICES, Check, CheckResult
from .serializers import CheckResultSerializer, CheckSerializer


@login_required
def checks(request):
    checks = Check.objects.order_by("-created")
    return render(request, "checks-list.html", {"checks": checks})


@login_required
def checks_add(request):
    if request.method == "POST":
        form = CheckForm(request.POST)
        if form.is_valid():
            check = form.save()
            add_info(request, f"Added health check `{check.name}`")
            return redirect(reverse("health:checks-list"))
    else:
        form = CheckForm()

    return render(
        request, "checks-add.html", {"form": form, "repo": settings.GITHUB_CHECK_REPOSITORY}
    )


@login_required
def checks_detail(request, slug):
    check = Check.objects.get(slug=slug)
    return render(request, "checks-detail.html", {"check": check})


@login_required
def checks_update(request, slug):
    check = Check.objects.get(slug=slug)
    if request.method == "POST":
        form = CheckForm(request.POST, instance=check)
        if form.is_valid():
            check = form.save()
            add_info(request, f"Updated health check `{check.name}`")
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-update.html", {"check": check, "form": form})

    form = CheckForm(instance=check)
    return render(request, "checks-update.html", {"check": check, "form": form})


@login_required
@require_POST
def checks_delete(request, slug):
    check = Check.objects.get(slug=slug)
    add_info(request, f"Health check `{slug}` and matching results deleted")
    Check.objects.get(slug=slug).delete()
    return redirect(reverse("health:checks-list"))


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
        "choices": {"result": RESULT_CHOICES, "status": STATUS_CHOICES},
    }
    return render(request, "results.html", context)


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all().order_by("-created")
    serializer_class = CheckSerializer
    permission_classes = [permissions.IsAuthenticated]


class CheckResultViewSet(viewsets.ModelViewSet):
    queryset = CheckResult.objects.all().order_by("-created")
    serializer_class = CheckResultSerializer
    permission_classes = [permissions.IsAuthenticated]
