from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
import os
from django.conf import settings

def home(request):
    return render(request, "home.html", {"breadcrumbs": False})


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
        if not value: return "Empty"
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
    return render(request, "debug.html", {
        "envs": selected_envs, 
        "settings": selected_settings
    })
