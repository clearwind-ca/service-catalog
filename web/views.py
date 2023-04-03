import os
from django.contrib import messages

from django.conf import settings
from django.contrib import auth
from django.shortcuts import redirect, render, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token
from systemlogs.models import add_info
from .shortcuts import get_object_or_None

def home(request):
    return render(request, "home.html")


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)


def logout(request):
    auth.logout(request)
    return redirect("/")


def debug(request):
    get = os.environ.get

    def truncate(key):
        value = get(key)
        if not value:
            return "Empty"
        return value[:2] + "..."

    selected_envs = {
        "CATALOG_ENV": get("CATALOG_ENV"),
        "DEBUG": get("DEBUG"),
        "DATABASE_URL": truncate("DATABASE_URL"),
        "ALLOWED_HOSTS": get("ALLOWED_HOSTS"),
        "GITHUB_APP_ID": truncate("GITHUB_APP_ID"),
        "GITHUB_CLIENT_ID": truncate("GITHUB_CLIENT_ID"),
        "GITHUB_CLIENT_SECRET": truncate("GITLAB_CLIENT_SECRET"),
    }
    selected_settings = {
        "CATALOG_ENV": settings.CATALOG_ENV,
        "DEBUG": settings.DEBUG,
    }
    return render(
        request, "debug.html", {"envs": selected_envs, "settings": selected_settings}
    )

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
    messages.add_message(request, messages.SUCCESS, f"Token created: `{token.key}` this is the only time this will appear, so make a copy of it now.")
    add_info(request.user, "Created API token.", request=request)
    return render(request, "api.html", {"token": token})
    
@login_required
@require_POST
def api_delete(request):
    Token.objects.filter(user=request.user).delete()
    messages.add_message(request, messages.SUCCESS, "Token deleted")
    add_info(request.user, "Deleted API token.", request=request)
    return redirect(reverse("web:api"))