from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


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


class CampaignInvite(models.Model):

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="invites"
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    def is_valid(self):
        if not self.is_active:
            return False
        return self.expires_at > timezone.now()

    def __str__(self):
        return f"Invite to {self.campaign.name}"
