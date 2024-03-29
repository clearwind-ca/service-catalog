import os

import requests
from django.contrib import auth, messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token

from gh import app
from services.models import Organization

from .forms import CreateAppForm
from .shortcuts import get_object_or_None


def home(request):
    context = {}
    if request.user.is_authenticated:
        # We could show all but that's gonna be pretty big.
        context["orgs"] = [Organization.objects.last()]

    return render(request, "home.html", context)


def login_problem(request):
    return render(request, "403.html")


def handler403(request, exception):
    return render(request, "403.html", status=403, context={"hide_login": True})


def handler404(request, exception):
    return render(request, "404.html", status=404, context={"hide_login": True})


def handler500(request):
    return render(request, "500.html", status=500, context={"hide_login": True})


def logout(request):
    auth.logout(request)
    return redirect("/")


def get(key):
    return bool(os.environ.get(key, None))


def setup(request):
    form = CreateAppForm()
    app_details = app.get_details()
    context = {
        "keys": {
            "django": {
                "SECRET_KEY": get("SECRET_KEY"),
                "DATABASE_URL": get("DATABASE_URL"),
                "SERVER_URL": get("SERVER_URL"),
                "CELERY_BROKER_URL": get("CELERY_BROKER_URL"),
                "ALLOWED_HOSTS": get("ALLOWED_HOSTS"),
            },
            "github": {
                "GITHUB_APP_ID": get("GITHUB_APP_ID"),
                "GITHUB_CLIENT_ID": get("GITHUB_CLIENT_ID"),
                "GITHUB_CLIENT_SECRET": get("GITHUB_CLIENT_SECRET"),
                "GITHUB_PEM": get("GITHUB_PEM"),
                "GITHUB_WEBHOOK_SECRET": get("GITHUB_WEBHOOK_SECRET"),
            },
            "app": {},
        },
        "app_details": app_details,
        "steps": {
            "django": False,
            "github": False,
            "orgs": Organization.objects.exists(),
            "app": bool(app_details),
        },
        "form": form,
    }
    if request.GET and request.GET.get("code"):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        res = requests.post(
            f'https://api.github.com/app-manifests/{request.GET["code"]}/conversions',
            headers=headers,
        )
        if res.status_code != 201:
            messages.error(request, "Something went wrong creating the app.")

        else:
            context["app"] = res.json()
            messages.info(
                request,
                "App successfully created. You must now copy the app values into the environment variables as shown below. <b>This is the only time they will be shown</b>.",
            )

    context["steps"]["django"] = all(
        [context["keys"]["django"][v] for v in context["keys"]["django"]]
    )
    context["steps"]["github"] = all(
        [context["keys"]["github"][v] for v in context["keys"]["github"]]
    )

    return render(request, "setup.html", context)


@require_POST
def setup_orgs(request):
    # This doesn't have any permissions on it, so it will need to work before the organizations are created.
    if Organization.objects.exists():
        messages.add_message(
            request, messages.ERROR, "Organizations already exist, so initial setup is unavailable."
        )
        return redirect(reverse("web:setup"))

    for org in app.get_orgs():
        Organization.objects.get_or_create(url=org.html_url, name=org.login)

    return redirect(reverse("web:setup"))


@permission_required("authtoken.add_token")
def api(request):
    token = get_object_or_None(Token, user=request.user)
    if request.method == "GET":
        return render(request, "api.html", {"token": token})


@require_POST
@permission_required("authtoken.add_token")
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


@require_POST
@permission_required("authtoken.add_token")
def api_delete(request):
    Token.objects.filter(user=request.user).delete()
    messages.add_message(request, messages.SUCCESS, "Deleted API token.")
    return redirect(reverse("web:api"))
