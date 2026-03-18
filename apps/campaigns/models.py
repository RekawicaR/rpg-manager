from django.db import models
from django.conf import settings


class Campaign(models.Model):

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_campaigns"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CampaignMembership(models.Model):

    class Role(models.TextChoices):
        DM = "DM"
        PLAYER = "PLAYER"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    # No duplicates for campaign members
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "campaign"],
                name="unique_user_campaign"
            )
        ]
