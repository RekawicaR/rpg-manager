from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.campaigns.models import Campaign, CampaignMembership


User = get_user_model()


class CampaignAPITestCase(APITestCase):
    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

    def create_user(self, username, password="TestPassword123", email=None):
        if email is None:
            email = f"{username}@example.com"
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    def create_campaign_with_members(self, dm, players=None, **campaign_kwargs):
        campaign = Campaign.objects.create(
            name=campaign_kwargs.get("name", "Test Campaign"),
            description=campaign_kwargs.get("description", "Test description"),
            created_by=dm,
        )
        CampaignMembership.objects.create(
            user=dm,
            campaign=campaign,
            role=CampaignMembership.Role.DM,
        )

        for player in players or []:
            CampaignMembership.objects.create(
                user=player,
                campaign=campaign,
                role=CampaignMembership.Role.PLAYER,
            )

        return campaign
