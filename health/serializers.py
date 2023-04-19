from rest_framework import serializers

from .models import Check, CheckResult


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = "__all__"


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = "__all__"
        read_only_fields = ["status"]
