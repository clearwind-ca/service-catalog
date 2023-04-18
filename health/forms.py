from django.forms import ModelForm
from .models import HealthCheck

class HealthCheckForm(ModelForm):
    class Meta:
        model = HealthCheck
        fields = ['name', 'description', 'frequency']