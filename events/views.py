from datetime import timedelta

from auditlog.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from services.models import Service
from systemlogs.models import add_info
from web.helpers import process_query_params

from .forms import EventForm
from .models import EVENT_TYPES, Event


@login_required
def events_add(request):
    if request.POST:
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            add_info(request, "Event created successfully")
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
def events_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.POST:
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            add_info(request, "Event updated successfully")
            return redirect(reverse("events:events-list"))
    else:
        form = EventForm(instance=event)

    return render(request, "events-update.html", {"form": form, "event": event})


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
    elif get.get("when") == "soon":
        filters["start__gte"] = timezone.now()
        filters["start__lte"] = timezone.now() + timedelta(days=2)
        display_filters["when"] = "soon"

    if get.get("service"):
        service = get_object_or_404(Service, slug=get["service"])
        filters["services__in"] = [service]
        display_filters["service"] = get["service"]

    ordering = "-start"
    if get.get("when") in ["future", "soon"]:
        ordering = "start"

    results = Event.objects.filter(**filters).order_by(ordering)

    paginator = Paginator(results, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "events": page_obj,
        "filters": display_filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "types": sorted(dict(EVENT_TYPES).keys()),
        "when": ["future", "soon", "past"],
        "active": ["yes", "no"],
        "customers": ["yes", "no"],
        "ordering": "ordering",
    }
    return render(request, "events-list.html", context)
