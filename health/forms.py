from django import forms

from .models import Check
from django.template.defaultfilters import slugify

class CheckForm(forms.ModelForm):
    class Meta:
        model = Check
        fields = ["name", "description", "frequency", "active", "limit", "services"]

    def is_valid(self):
        slug = slugify(self.data.get("name"))
        if Check.objects.filter(slug=slug).exists():
            self.add_error("name", "A check with this name already exists.")


ACTION_CHOICES = (
    ("examine-json", "Examine the JSON file for a service"),
    ("checkout-repo", "Check out the source code of a service"),
)


class ActionForm(forms.Form):
    type = forms.ChoiceField(
        choices=ACTION_CHOICES, widget=forms.RadioSelect(choices=ACTION_CHOICES)
    )
