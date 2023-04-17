from rest_framework import serializers


class SystemLogSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import SystemLog

        model = SystemLog
        fields = "__all__"
