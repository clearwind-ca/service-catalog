import json
import os

import jsonschema
from django import forms
from django.conf import settings

from . import models


class BaseForm:
    def nice_errors(self):
        return ". ".join([". ".join(v) for k, v in self.errors.items()])


class SourceForm(forms.ModelForm, BaseForm):
    class Meta:
        model = models.Source
        fields = ("name", "host")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not self.data.get("host"):
            raise forms.ValidationError("A host must be selected.")
        if models.Source.objects.filter(name=name, host=self.data["host"]).exists():
            raise forms.ValidationError("A source with this name already exists.")
        if "/" not in name and self.data["host"] == "G":
            raise forms.ValidationError("Name must be GitHub owner/repository.")
        return name


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
