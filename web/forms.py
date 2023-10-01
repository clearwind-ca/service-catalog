from django import forms
from django.conf import settings


class CreateAppForm(forms.Form):
    organization = forms.CharField(label="Organization")
    server_url = forms.CharField(
        label="Catalog URL",
        help_text="Set by the environment variable SERVER_URL.",
        widget=forms.TextInput(attrs={"value": settings.SERVER_URL, "readonly": "readonly"}),
    )
