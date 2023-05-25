from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ProfileForm


def profile_detail(request):
    context = {
        "profile": request.user.profile,
        "form": ProfileForm(instance=request.user.profile),
    }
    return render(request, "profile-details.html", context=context)


@require_POST
def profile_update(request):
    form = ProfileForm(instance=request.user.profile, data=request.POST)
    context = {
        "profile": request.user.profile,
        "form": form,
    }
    if form.is_valid():
        form.save()
        messages.info(request, "Profile updated successfully")
        return redirect(reverse("profile:profile-detail"))

    return render(request, "profile-details.html", context=context)
