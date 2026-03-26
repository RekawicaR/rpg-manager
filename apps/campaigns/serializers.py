from django.db import transaction
from rest_framework import serializers
from .models import Campaign, CampaignSource
from apps.compendium.models.source import Source


class CampaignSerializer(serializers.ModelSerializer):

    # save username instead of id and make it Read Only
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "created_by",
            "created_at"
        ]


class CampaignSourceUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating list of allowed Sources for Campaign.
    - Validates that all ID exist in DB
    - When an empty list is send then all Sources are deleted form Campaign
    """

    source_ids = serializers.PrimaryKeyRelatedField(
        queryset=Source.objects.all(),
        many=True
    )

    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        sources = validated_data["source_ids"]

        # Do it as one transaction (delete + create)
        with transaction.atomic():
            CampaignSource.objects.filter(campaign=instance).delete()

            CampaignSource.objects.bulk_create([
                CampaignSource(campaign=instance, source=source)
                for source in sources
            ])

        return instance

    def validate_source_ids(self, value):
        unique_ids = set([s.id for s in value])

        if len(unique_ids) != len(value):
            raise serializers.ValidationError(
                "Duplicate sources are not allowed.")

        return value
