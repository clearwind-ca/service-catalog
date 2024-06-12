import importlib
import logging
from datetime import timedelta
from distutils.util import strtobool

import django_filters
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets

from web.helpers import YES_NO_CHOICES, paginate

from .forms import EventForm
from .handlers import dump_webhook
from .models import Event
from .serializers import EventSerializer

logger = logging.getLogger(__name__)


@permission_required("events.add_event")
def events_add(request):
    if request.POST:
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(request, "Event created successfully")
            return redirect(reverse("events:events-list"))
    else:
        form = EventForm()
        form.fields["start"].initial = timezone.now()

    return render(request, "events-add.html", {"form": form})


def events_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
        "log": LogEntry.objects.get_for_object(event).order_by("-timestamp").first(),
    }
    return render(request, "events-detail.html", context)


@require_POST
@permission_required("events.delete_event")
def events_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.info(request, f"Event `{event.name}` successfully deleted")
    return redirect(reverse("events:events-list"))


@permission_required("events.change_event")
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


def imp(module):
    return importlib.import_module(f"events.handlers.{module}")


webhook_handlers = {
    "launchdarkly": imp("flag-launchdarkly"),
    "bitbucket": imp("status-atlassian"),
    "confluence": imp("status-atlassian"),
    "fly.io": imp("status-atlassian"),
    "github": imp("status-atlassian"),
    "jira": imp("status-atlassian"),
    "netlify": imp("status-atlassian"),
    "trello": imp("status-atlassian"),
    "vercel": imp("status-atlassian"),
}


@csrf_exempt
def webhooks(request, slug):
    if settings.DUMP_WEBHOOKS:
        dump_webhook(request, slug)

    if slug in webhook_handlers:
        logger.info(f"Found handler for {slug}")
        webhook_handlers[slug].handle(request)
    else:
        logger.info(f"No handler for {slug}")

    return HttpResponse("OK")


class EventsFilter(django_filters.FilterSet):
    active = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)
    customers = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)

    class Meta:
        model = Event
        fields = ["type", "source"]


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

    # Doesn't seem to work in django-filters, I'm clearly holding it wrong.
    if get.get("services"):
        filters["services__slug"] = get.get("services")

    queryset = Event.objects.filter(**filters).order_by(ordering)
    events = EventsFilter(request.GET, queryset=queryset)

    context = paginate(request, events, extra={"when": get.get("when", "recent")})
    context.update(
        {
            "types": sorted(
                Event.objects.filter(type__gt="").values_list("type", flat=True).distinct()
            ),
            "source": sorted(
                Event.objects.filter(source__gt="").values_list("source", flat=True).distinct()
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
    permission_classes = [permissions.DjangoModelPermissions]
