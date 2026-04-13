from django.db import models
from apps.compendium.models.source import Source


class BaseCompendiumItem(models.Model):

    name = models.CharField(max_length=200)

    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
