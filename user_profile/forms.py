from django import forms

from . import models


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        exclude = ["updated", "created", "user", "avatar"]
