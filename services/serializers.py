from rest_framework import serializers

from .models import Service, Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = "__all__"
        read_only_fields = ["slug", "created", "updated"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"
        read_only_fields = ["slug", "created", "updated"]

