from django.forms import ModelForm

from .models import Check


class CheckForm(ModelForm):
    class Meta:
        model = Check
        fields = ["name", "description", "frequency"]
