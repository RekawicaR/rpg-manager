from django.db import transaction
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Campaign, CampaignSource, CampaignItemRule
from apps.compendium.models.source import Source
from apps.compendium.services import get_compendium_models


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


class CampaignItemRuleCreateSerializer(serializers.Serializer):
    '''CampaignItemRule Input serializer.'''

    content_type = serializers.CharField()
    object_id = serializers.IntegerField()
    rule_type = serializers.ChoiceField(
        choices=CampaignItemRule.RuleType.choices
    )

    def validate(self, data):

        # To not add CompendiumItems for validate every time a new type of CompendiumItem is added
        # this Auto-discovery feature is used to get all CompendiumItem from Compendium app
        model_map = get_compendium_models()

        model_class = model_map.get(data["content_type"].lower().strip())

        if not model_class:
            raise serializers.ValidationError("Invalid content type")

        ct = ContentType.objects.get_for_model(
            model_class,
            for_concrete_model=False
        )

        # check if object exists
        if not model_class.objects.filter(id=data["object_id"]).exists():
            raise serializers.ValidationError("Item does not exist")

        data["content_type_obj"] = ct

        return data

    def create(self, validated_data):

        campaign = self.context["campaign"]

        return CampaignItemRule.objects.update_or_create(
            campaign=campaign,
            content_type=validated_data["content_type_obj"],
            object_id=validated_data["object_id"],
            defaults={"rule_type": validated_data["rule_type"]}
        )[0]


class CampaignItemRuleSerializer(serializers.ModelSerializer):
    '''CampaignItemRule Output serializer.'''

    content_type = serializers.SerializerMethodField()

    def get_content_type(self, obj):
        return obj.content_type.model

    class Meta:
        model = CampaignItemRule
        fields = ["id", "content_type", "object_id", "rule_type"]
