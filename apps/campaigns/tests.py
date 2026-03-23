from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from apps.campaigns.models import Campaign, CampaignMembership, CampaignInvite


User = get_user_model()


class CampaignDMTests(APITestCase):

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
                role=CampaignMembership.Role.DM
            ).exists()
        )

    def test_invite_to_campaign(self):

        payload = {
            "name": "My Campaign",
            "description": "Test campaign"
        }
        response = self.client.post("/api/campaigns/create/", payload)
        self.assertEqual(response.status_code, 201)

        campaign = Campaign.objects.first()

        response = self.client.post(
            reverse("campaign-invite-create", kwargs={"campaign_id": campaign.id}))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignInvite.objects.count(), 1)

        # Create another link
        response = self.client.post(
            reverse("campaign-invite-create", kwargs={"campaign_id": campaign.id}))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignInvite.objects.count(), 2)

    def test_invite_invalid_when_expired(self):
        payload = {
            "name": "My Campaign",
            "description": "Test campaign"
        }
        response = self.client.post("/api/campaigns/create/", payload)
        self.assertEqual(response.status_code, 201)

        campaign = Campaign.objects.first()

        invite = CampaignInvite.objects.create(
            campaign=campaign,
            invited_by=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )

        self.assertFalse(invite.is_valid())

    def test_invite_invalid_when_non_active(self):
        payload = {
            "name": "My Campaign",
            "description": "Test campaign"
        }
        response = self.client.post("/api/campaigns/create/", payload)
        self.assertEqual(response.status_code, 201)

        campaign = Campaign.objects.first()

        invite = CampaignInvite.objects.create(
            campaign=campaign,
            invited_by=self.user,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=False
        )

        self.assertFalse(invite.is_valid())


class CampaignPlayerTests(APITestCase):

    def setUp(self):

        self.user1 = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="Test1Password123"
        )

        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="Test2Password123"
        )

        self.campaign = Campaign.objects.create(
            name="My Campaign",
            description="Test campaign",
            created_by=self.user1
        )

        CampaignMembership.objects.create(
            user=self.user1,
            campaign=self.campaign,
            role=CampaignMembership.Role.DM
        )

        token = RefreshToken.for_user(self.user2)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

    def test_accept_campaign_invite(self):

        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.user1,
            expires_at=timezone.now() + timedelta(days=7)
        )

        response = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token}))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["joined"], True)
        # Should be DM and one Player
        self.assertEqual(CampaignMembership.objects.count(), 2)
        self.assertTrue(
            CampaignMembership.objects.filter(
                user=self.user2,
                campaign=self.campaign,
                role=CampaignMembership.Role.PLAYER
            ).exists()
        )

        # Use the same link again
        response = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token}))

        # You shouldn't be able to join again as the same user
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["joined"], False)
        # Should still be DM and one Player (no duplicates)
        self.assertEqual(CampaignMembership.objects.count(), 2)
        self.assertTrue(
            CampaignMembership.objects.filter(
                user=self.user2,
                campaign=self.campaign,
                role=CampaignMembership.Role.PLAYER
            ).exists()
        )

    def test_expired_invite(self):

        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.user1,
            expires_at=timezone.now() - timedelta(days=1)
        )

        response = self.client.post(
            f"/api/campaigns/invites/{invite.token}/accept/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invite expired")

    def test_non_active_invite(self):
        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.user1,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=False
        )

        response = self.client.post(
            f"/api/campaigns/invites/{invite.token}/accept/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invite expired")
