from django.apps import apps
from apps.compendium.models.base_compendium_item import BaseCompendiumItem


def get_compendium_models():
    '''Auto-discovery of CompendiumItems.'''
    return {
        model._meta.model_name: model
        for model in apps.get_app_config("compendium").get_models()
        if issubclass(model, BaseCompendiumItem) and model is not BaseCompendiumItem
    }
