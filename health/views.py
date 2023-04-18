from django.shortcuts import render, redirect
from django.urls import reverse
from .models import HealthCheck, HealthCheckResult
from .forms import HealthCheckForm
from django.contrib.auth.decorators import login_required

from systemlogs.models import add_info

@login_required
def checks(request):
    checks = HealthCheck.objects.order_by("-created")
    return render(request, "checks-list.html", {"checks": checks})

@login_required
def checks_add(request):
    if request.method == "POST":
        form = HealthCheckForm(request.POST)
        if form.is_valid():
            check = form.save()
            msg = f"Added health check `{check.name}`"
            add_info(check, msg, web=True, request=request)
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-add.html", {"form": form})
    return render(request, "checks-add.html", {"form": HealthCheckForm()})

@login_required
def checks_detail(request, slug):
    check = HealthCheck.objects.get(slug=slug)
    if request.method == "POST":
        form = HealthCheckForm(request.POST, instance=check)
        if form.is_valid():
            check = form.save()
            msg = f"Updated health check `{check.name}`"
            add_info(check, msg, web=True, request=request)
            return redirect(reverse("health:checks-list"))
        return render(request, "checks-detail.html", {"check": check, "form": form})
    form = HealthCheckForm(instance=check)
    return render(request, "checks-detail.html", {"check": check, "form": form})

@login_required
def results(request):
    results = HealthCheckResult.objects.all()
    return render(request, "results.html", {"checks": results})

