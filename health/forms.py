from django import forms

from .models import Check


class CheckForm(forms.ModelForm):
    class Meta:
        model = Check
        fields = ["name", "description", "frequency", "active"]


ACTION_CHOICES = (
    ("examine-json", "Examine the JSON file for a service"),
    ("checkout-repo", "Check out the source code of a service"),
)


class ActionForm(forms.Form):
    type = forms.ChoiceField(
        choices=ACTION_CHOICES, widget=forms.RadioSelect(choices=ACTION_CHOICES)
    )
