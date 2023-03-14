from django.forms import ModelForm, ValidationError

from . import models


class SourceForm(ModelForm):
    class Meta:
        model = models.Source
        fields = ("name", "host")

    def clean_name(self):
        name = self.cleaned_data["name"]
        if models.Source.objects.filter(name=name, host=self.data["host"]).exists():
            raise ValidationError("A source with this name already exists.")
        if "/" not in name and self.data["host"] == "G":
            raise ValidationError("Name must be GitHub owner/repository.")
        return name

    def nice_errors(self):
        return ". ".join([". ".join(v) for k, v in self.errors.items()])
