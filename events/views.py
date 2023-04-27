from datetime import timedelta

from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from services.models import Service
from web.helpers import process_query_params

from .forms import EventForm
from .models import EVENT_TYPES, Event
from .serializers import EventSerializer

@login_required
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


@login_required
def events_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
        "log": LogEntry.objects.get_for_object(event).order_by("-timestamp").first(),
    }
    return render(request, "events-detail.html", context)


@login_required
@require_POST
def events_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.info(request, f"Event `{event.name}` successfully deleted")
    return redirect(reverse("events:events-list"))


@login_required
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
        "form": form
    }
    return render(request, "events-update.html", context)


@login_required
@process_query_params
def events_list(request):
    filters, display_filters = {}, {}
    get = request.GET
    for param, lookup in (
        ("active", "active"),
        ("type", "type"),
        ("customers", "customers"),
    ):
        if get.get(param) is not None:
            filters[lookup] = get[param]
            display_filters[param] = get[param]

    if get.get("when") == "past":
        filters["start__lt"] = timezone.now()
        display_filters["when"] = "past"

    elif get.get("when") == "future":
        filters["start__gte"] = timezone.now()
        display_filters["when"] = "future"

    elif get.get("when", None) in [None, "recent"]:
        # Default to 2 days either side from now
        filters["start__gte"] = timezone.now() - timedelta(days=2)
        filters["start__lte"] = timezone.now() + timedelta(days=2)
        display_filters["when"] = "recent"
    
    else:
        display_filters["when"] = "all"

    if get.get("service"):
        service = get_object_or_404(Service, slug=get["service"])
        filters["services__in"] = [service]
        display_filters["service"] = get["service"]

    ordering = "start"
    if get.get("when") == "past":
        ordering = "-start"

    results = Event.objects.filter(**filters).order_by(ordering)

    paginator = Paginator(results, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "events": page_obj,
        "filters": display_filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "types": dict(EVENT_TYPES).keys(),
        "when": ["future", "recent", "past"],
        "active": ["yes", "no"],
        "customers": ["yes", "no"],
        "ordering": ordering,
    }
    return render(request, "events-list.html", context)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-created")
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
