from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import permissions, viewsets

from systemlogs.models import add_info

from .forms import CheckForm
from .models import Check, CheckResult
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
            msg = f"Added health check `{check.name}`"
            add_info(check, msg, web=True, request=request)
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-add.html", {"form": form})
    return render(request, "checks-add.html", {"form": CheckForm()})


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
            msg = f"Updated health check `{check.name}`"
            add_info(check, msg, web=True, request=request)
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-update.html", {"check": check, "form": form})

    form = CheckForm(instance=check)
    return render(request, "checks-update.html", {"check": check, "form": form})


@login_required
def checks_delete(request, slug):
    check = Check.objects.get(slug=slug)
    msg = f"Health check `{slug}` and matching results deleted"
    add_info(check, msg, web=True, request=request)
    Check.objects.get(slug=slug).delete()
    return redirect(reverse("health:checks-list"))


@login_required
def results(request):
    results = CheckResult.objects.order_by("-created")
    return render(request, "results.html", {"results": results})


class CheckViewSet(viewsets.ModelViewSet):
    queryset = Check.objects.all().order_by("-created")
    serializer_class = CheckSerializer
    permission_classes = [permissions.IsAuthenticated]


class CheckResultViewSet(viewsets.ModelViewSet):
    queryset = CheckResult.objects.all().order_by("-created")
    serializer_class = CheckResultSerializer
    permission_classes = [permissions.IsAuthenticated]
