from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from catalog.errors import NoRepository, SendError
from gh import send
from services.models import Service
from systemlogs.models import add_error, add_info
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
    Check.objects.get(slug=slug).delete()
    add_info(request, f"Health check `{slug}` and matching results deleted")
    return redirect(reverse("health:checks-list"))


@login_required
@require_POST
def checks_run(request, slug):
    check = Check.objects.get(slug=slug)
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
            add_error(request, f"Failed to send health check: `{error.message}`")
            return redirect(reverse("health:checks-detail", kwargs={"slug": slug}))

    add_info(request, f"Health check `{slug}` run for all services.")
    return redirect(reverse("health:checks-detail", kwargs={"slug": slug}))


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
