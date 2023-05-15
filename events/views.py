from datetime import timedelta
from distutils.util import strtobool

import django_filters
from auditlog.models import LogEntry
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from web.helpers import YES_NO_CHOICES, paginate

from .forms import EventForm
from .models import Event
from .serializers import EventSerializer


def events_add(request):
    if request.POST:
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(request, "Event created successfully")
            return redirect(reverse("events:events-list"))
    else:
        form = EventForm()

    return render(request, "events-add.html", {"form": form})


def events_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
        "log": LogEntry.objects.get_for_object(event).order_by("-timestamp").first(),
    }
    return render(request, "events-detail.html", context)


@require_POST
def events_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.info(request, f"Event `{event.name}` successfully deleted")
    return redirect(reverse("events:events-list"))


def events_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.POST:
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.info(request, "Event updated successfully")
            return redirect(reverse("events:events-detail", kwargs={"pk": event.pk}))
    else:
        form = EventForm(instance=event)
    context = {
        "event": event,
        "log": LogEntry.objects.get_for_object(event).order_by("-timestamp").first(),
        "form": form,
    }
    return render(request, "events-update.html", context)


class EventsFilter(django_filters.FilterSet):
    active = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)
    customers = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)

    class Meta:
        model = Event
        fields = ["active", "type", "customers", "services"]


def events_list(request):
    get = request.GET
    filters = {}

    if get.get("when") == "past":
        filters["start__lt"] = timezone.now()

    elif get.get("when") == "future":
        filters["start__gte"] = timezone.now()

    elif get.get("when", None) in [None, "recent"]:
        # Default to 2 days either side from now
        filters["start__gte"] = timezone.now() - timedelta(days=2)
        filters["start__lte"] = timezone.now() + timedelta(days=2)

    ordering = "-start"
    if get.get("when") in ["future"]:
        ordering = "start"

    queryset = Event.objects.filter(**filters).order_by(ordering)
    events = EventsFilter(request.GET, queryset=queryset)
    context = paginate(request, events, extra={"when": get.get("when", "recent")})
    context.update(
        {
            "types": sorted(
                Event.objects.filter(type__gt="").values_list("type", flat=True).distinct()
            ),
            "when": ["future", "recent", "past"],
            "customers": ["yes", "no"],
            "ordering": ordering,
        }
    )
    return render(request, "events-list.html", context)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-created")
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
