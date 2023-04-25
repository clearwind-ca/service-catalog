from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from web.helpers import process_query_params
from .models import Event, EVENT_TYPES
from .forms import EventForm
from systemlogs.models import add_info
from django.utils import timezone

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
def events_update(request, slug):
    event = Event.objects.get(slug=slug)
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
def events_details(request, slug):
    return render(request, "events-details.html")


@login_required
@process_query_params
def events_list(request):
    filters, display_filters = {}, {}
    get = request.GET
    for param, lookup in (
        ("active", "active"),
        ("type", "type"),
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

    results = Event.objects.filter(**filters).order_by("-start")

    paginator = Paginator(results, per_page=get["per_page"])
    page_number = get["page"]
    page_obj = paginator.get_page(page_number)

    context = {
        "events": page_obj,
        "filters": display_filters,
        "page_range": page_obj.paginator.get_elided_page_range(get["page"]),
        "types": sorted(dict(EVENT_TYPES).keys()),
        "when": ["future", "past"],
        "active": ["yes", "no"]
    }
    return render(request, "events-list.html", context)
