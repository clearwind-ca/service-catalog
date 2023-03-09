from django.forms import ModelForm, ValidationError

from . import models


class SourceForm(ModelForm):
    class Meta:
        model = models.Source
        fields = ("name", "service")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if "/" not in name and self.data["service"] == "G":
            raise ValidationError("Source name must be GitHub owner/name.")
        return name
