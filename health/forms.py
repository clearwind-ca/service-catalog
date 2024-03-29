from django import forms
from django.template.defaultfilters import slugify

from .models import Check


class CheckForm(forms.ModelForm):
    class Meta:
        model = Check
        fields = ["name", "description", "frequency", "active", "limit", "services"]

    def is_valid(self):
        slug = slugify(self.data.get("name"))
        if Check.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            self.add_error("name", "A check with this name already exists.")

        return super().is_valid()


ACTION_CHOICES = (
    ("examine-json", "Examine the JSON file for a service"),
    ("checkout-repo", "Check out the source code of a service"),
    ("no-service", "Create an Action that has no service"),
)


class ActionForm(forms.Form):
    type = forms.ChoiceField(
        choices=ACTION_CHOICES, widget=forms.RadioSelect(choices=ACTION_CHOICES)
    )
