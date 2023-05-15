from distutils.util import strtobool

import django_filters
from auditlog.models import LogEntry
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from rest_framework import permissions, viewsets

from web.helpers import YES_NO_CHOICES, paginate

from .serializers import LogEntrySerializer

model_map = {
    "service": "services",
    "source": "services",
    "event": "events",
    "check": "health",
    "check result": "health",
}


class LogFilter(django_filters.FilterSet):
    active = django_filters.TypedChoiceFilter(choices=YES_NO_CHOICES, coerce=strtobool)

    class Meta:
        model = LogEntry
        fields = ["action"]


def log_list(request):
    get = request.GET

    filters = {}
    # Not sure how to do these in django-filters.
    if request.GET.get("type"):
        target = get["type"]
        _model_name = model_map.get(target)
        assert _model_name
        _model = apps.get_model(model_name=target.replace(" ", ""), app_label=_model_name)
        filters["content_type__pk"] = ContentType.objects.get_for_model(_model).pk

    if get.get("slug"):
        _object = _model.objects.get(slug=get["slug"])
        filters["object_id"] = _object.pk

    if get.get("pk"):
        _object = _model.objects.get(pk=get["pk"])
        filters["object_id"] = _object.pk

    queryset = LogEntry.objects.filter(**filters).order_by("-timestamp")
    entries = LogFilter(request.GET, queryset=queryset)
    context = paginate(request, entries)
    context.update(
        {
            "actions": LogEntry.Action.choices,
            "types": sorted(model_map.keys()),
        }
    )
    return render(request, "log-list.html", context)


def log_details(request, pk):
    log = LogEntry.objects.get(pk=pk)
    return render(request, "log-details.html", {"log": log})


class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEntry.objects.all().order_by("-timestamp")
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
