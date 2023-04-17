from rest_framework import serializers

from .models import SystemLog


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLog
        fields = "__all__"
