from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.campaigns.models import Campaign, CampaignMembership


User = get_user_model()


class CampaignTests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123"
        )

        token = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

    def test_create_campaign(self):

        payload = {
            "name": "My Campaign",
            "description": "Test campaign"
        }

        response = self.client.post("/api/campaigns/create/", payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Campaign.objects.count(), 1)
        campaign = Campaign.objects.first()
        self.assertEqual(campaign.created_by, self.user)
        self.assertTrue(
            CampaignMembership.objects.filter(
                user=self.user,
                campaign=campaign,
                role="DM"
            ).exists()
        )
