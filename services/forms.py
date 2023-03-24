import json
import os

import jsonschema
from django import forms
from django.conf import settings
from urllib.parse import urlparse
from . import models


class BaseForm:
    def nice_errors(self):
        return ". ".join([". ".join(v) for k, v in self.errors.items()])


class SourceForm(forms.ModelForm, BaseForm):
    class Meta:
        model = models.Source
        fields = ("url",)

    def clean_url(self):
        url = self.data["url"]
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise forms.ValidationError("URL must be HTTP or HTTPS.")
        if not parsed.path:
            raise forms.ValidationError("URL must include a path to the repository.")
        if models.Source.objects.filter(slug=models.slugify_source(url)).count():
            raise forms.ValidationError(f"Source: `{url}` already exists.")

        return url


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
        except jsonschema.ValidationError as error:
            raise forms.ValidationError(error.message)

        return self.data["data"]
