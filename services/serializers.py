from rest_framework import serializers

from .models import Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = "__all__"
        read_only_fields = ["slug", "created", "updated"]
