from django.shortcuts import render


def deployments(request):
    return render(request, "deployments.html")
