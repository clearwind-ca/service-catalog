import json
import os
from urllib.parse import urlparse

import jsonschema
from django import forms
from django.conf import settings
from django.contrib import messages

from gh.fetch import url_to_nwo
from web.shortcuts import get_object_or_None

from . import models


class BaseForm:
    def nice_errors(self):
        return ". ".join([". ".join(v) for k, v in self.errors.items()])


class OrgForm(forms.ModelForm):
    class Meta:
        model = models.Organization
        exclude = ["created", "modified", "active"]

    def clean(self):
        if models.Organization.objects.exists():
            raise ValueError("Only one organization can be created.")
        return super().clean()


class SourceForm(forms.ModelForm, BaseForm):
    class Meta:
        model = models.Source
        exclude = ["created", "modified", "slug", "name", "org"]

    def clean_url(self):
        url = self.data["url"]
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise forms.ValidationError("URL must be HTTP or HTTPS.")
        if not parsed.path:
            raise forms.ValidationError("URL must include a path to the repository.")

        org, self.cleaned_data["name"] = url_to_nwo(self.data["url"])
        organization = get_object_or_None(models.Organization, name=org)
        self.org = organization
        return self.data["url"]

    def save(self):
        res = super().save()
        dirty = False
        if not self.instance.name and self.cleaned_data["name"]:
            dirty = True
            self.instance.name = self.cleaned_data["name"]
        if not self.instance.org and self.org:
            dirty = True
            self.instance.org = self.org
        if dirty:
            self.instance.save()
        return res


def get_schema():
    if not os.path.exists(settings.SERVICE_SCHEMA):
        raise ValueError(f"No schema file found at: {settings.SERVICE_SCHEMA}")

    with open(settings.SERVICE_SCHEMA, "r") as schema_file:
        return json.load(schema_file)


class ServiceForm(forms.Form, BaseForm):
    data = forms.CharField()

    def clean_data(self):
        schema = get_schema()
        try:
            jsonschema.validate(self.data["data"], schema)
        except json.JSONDecodeError:
            raise forms.ValidationError("Unable to decode the JSON.")
        except jsonschema.ValidationError as error:
            raise forms.ValidationError(error.message)

        self.data["slug"] = models.slugify_service(self.data["data"]["name"])
        return self.data["data"]

    def save(self):
        """
        This does all the heavy lifting for saving a service.
        It will create a new service if it does not exist, or update an existing service if it does exist.
        It will also add and remove dependencies as needed.

        It will require the source to be set on the form before calling save.
        Returns:
            dict: {
                "created": bool,
                "updated": bool,
                "service": Service,
                "logs": list
            }
        """
        logs = []
        created = False
        updated = False
        assert self.source, "Source must be set on the form."
        data = self.data["data"]
        slug = models.slugify_service(data["name"])
        try:
            service = models.Service.objects.get(slug=slug)
            for key in ["name", "description", "type", "priority", "meta", "active", "events"]:
                if data.get(key) != getattr(service, key, None):
                    value = data.get(key)
                    if key == "active" and not value:
                        value = True
                    setattr(service, key, value)
                    updated = True
            service.raw_data = data
            if updated:
                service.save()
                logs.append([f"Updated service: `{service}`.", messages.INFO])

        except models.Service.DoesNotExist:
            service = models.Service.objects.create(
                name=data["name"],
                description=data.get("description"),
                type=data.get("type"),
                priority=data["priority"],
                meta=data.get("meta"),
                source=self.source,
                active=data.get("active", True),
                events=data.get("events", []),
                raw_data=data,
            )
            created = True
            logs.append([f"Created service: `{service}`.", messages.INFO])

        if "dependencies" in data:
            for dependency in data["dependencies"]:
                try:
                    dependency = models.Service.objects.get(slug=dependency)
                except models.Service.DoesNotExist:
                    logs.append(
                        [
                            f"Dependency: `{dependency}` does not exist in the catalog and was not connected.",
                            messages.WARNING,
                        ]
                    )
                    continue
                service.dependencies.add(dependency)

        # Remove any depenedencies that are not in the catalog data.
        for dependency in service.dependencies.all():
            if dependency.slug not in data["dependencies"]:
                logs.append([f"Removed dependency `{dependency}`.", messages.INFO])
                service.dependencies.remove(dependency)

        return {
            "created": created,
            "service": service,
            "updated": updated,
            "logs": logs,
        }
