import os

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token

from .shortcuts import get_object_or_None


def handler403(request, exception):
    return render(request, "custom-403.html", status=403, context={"hide_login": True})


def handler404(request, exception):
    return render(request, "404.html", status=404, context={"hide_login": True})


def handler500(request):
    return render(request, "500.html", status=500, context={"hide_login": True})


def logout(request):
    auth.logout(request)
    return redirect("/")


def debug(request):
    get = os.environ.get

    def truncate(value):
        if not value:
            return "Empty"
        return value[:5] + "..."

    selected_envs = {
        "CATALOG_ENV": get("CATALOG_ENV"),
        "CRON_USER": get("CRON_USER"),
        "DATABASE_URL": truncate(get("DATABASE_URL")),
        "ALLOWED_HOSTS": get("ALLOWED_HOSTS"),
        "GITHUB_APP_ID": truncate(get("GITHUB_APP_ID")),
        "GITHUB_CLIENT_ID": truncate(get("GITHUB_CLIENT_ID")),
        "GITHUB_CLIENT_SECRET": truncate(get("GITHUB_CLIENT_SECRET")),
    }
    selected_settings = {
        "CATALOG_ENV": settings.CATALOG_ENV,
        "CELERY_BROKER_URL": truncate(settings.CELERY_BROKER_URL),
        "CELERY_RESULT_BACKEND": truncate(settings.CELERY_RESULT_BACKEND),
        "DEBUG": settings.DEBUG,
        "GITHUB_CHECK_REPOSITORY": settings.GITHUB_CHECK_REPOSITORY,
        "GITHUB_DEBUG": settings.GITHUB_DEBUG,
        "SERVICE_SCHEMA": settings.SERVICE_SCHEMA,
    }
    return render(request, "debug.html", {"envs": selected_envs, "settings": selected_settings})


@login_required
def api(request):
    token = get_object_or_None(Token, user=request.user)
    if request.method == "GET":
        return render(request, "api.html", {"token": token})


@login_required
@require_POST
def api_create(request):
    if Token.objects.filter(user=request.user).exists():
        messages.add_message(request, messages.ERROR, "Token already exists")
        return redirect(reverse("web:api"))

    token = Token.objects.create(user=request.user)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Token created: `{token.key}` this is the only time this will appear, so make a copy of it now.",
    )
    return render(request, "api.html", {"token": token})


@login_required
@require_POST
def api_delete(request):
    Token.objects.filter(user=request.user).delete()
    messages.add_message(request, messages.SUCCESS, "Deleted API token.")
    return redirect(reverse("web:api"))
