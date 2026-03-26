from rest_framework import serializers
from apps.compendium.models.source import Source


class SourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Source
        fields = ["id", "code", "name"]
