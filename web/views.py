from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def home(request):
    return render(request, "home.html", {"breadcrumbs": False})


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)


def logout(request):
    auth.logout(request)
    return redirect("/")


@login_required
def debug(request):
    return render(request, "debug.html", {"user": request.user})
