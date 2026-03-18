from rest_framework import serializers
from .models import Campaign


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
