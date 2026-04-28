from django.apps import apps
from apps.compendium.models.base_compendium_item import BaseCompendiumItem
from apps.campaigns.models import Campaign, CampaignItemRule
from django.contrib.contenttypes.models import ContentType


def get_compendium_models():
    '''Auto-discovery of CompendiumItems.'''
    return {
        model._meta.model_name: model
        for model in apps.get_app_config("compendium").get_models()
        if issubclass(model, BaseCompendiumItem) and model is not BaseCompendiumItem
    }


def get_allowed_compendium_items_for_campaign(campaign: Campaign, model_class):

    content_type = ContentType.objects.get_for_model(model_class)

    allowed_sources = campaign.sources.values_list("id", flat=True)
    blocked_items = CampaignItemRule.objects.filter(
        campaign=campaign,
        content_type=content_type,
        rule_type=CampaignItemRule.RuleType.BLOCK
    ).values_list("object_id", flat=True)
    allowed_items = CampaignItemRule.objects.filter(
        campaign=campaign,
        content_type=content_type,
        rule_type=CampaignItemRule.RuleType.ALLOW
    ).values_list("object_id", flat=True)

    return (
        model_class.objects.filter(source_id__in=allowed_sources).exclude(
            id__in=blocked_items) | model_class.objects.filter(id__in=allowed_items)
    ).select_related("source").distinct()
