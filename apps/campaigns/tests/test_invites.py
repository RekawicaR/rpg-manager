from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.campaigns.models import CampaignInvite, CampaignMembership
from apps.campaigns.tests.base import CampaignAPITestCase


class CampaignInviteTests(CampaignAPITestCase):
    def setUp(self):
        self.dm = self.create_user("dm")
        self.player = self.create_user("player")
        self.outsider = self.create_user("outsider")
        self.campaign = self.create_campaign_with_members(self.dm, [self.player])

    def test_dm_can_create_multiple_invites(self):
        self.authenticate(self.dm)
        url = reverse("campaign-invite-create", kwargs={"campaign_id": self.campaign.id})

        first = self.client.post(url)
        second = self.client.post(url)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(CampaignInvite.objects.count(), 2)

    def test_player_cannot_create_invite(self):
        self.authenticate(self.player)

        response = self.client.post(
            reverse("campaign-invite-create", kwargs={"campaign_id": self.campaign.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_create_invite(self):
        self.authenticate(self.outsider)

        response = self.client.post(
            reverse("campaign-invite-create", kwargs={"campaign_id": self.campaign.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_accept_campaign_invite(self):
        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.dm,
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.authenticate(self.outsider)

        response = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token})
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["joined"])
        self.assertTrue(
            CampaignMembership.objects.filter(
                user=self.outsider,
                campaign=self.campaign,
                role=CampaignMembership.Role.PLAYER,
            ).exists()
        )

    def test_accept_campaign_invite_is_idempotent(self):
        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.dm,
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.authenticate(self.outsider)

        first = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token})
        )
        second = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token})
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.json()["joined"])

    def test_expired_invite_returns_400(self):
        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.dm,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.authenticate(self.outsider)

        response = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token})
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invite expired")

    def test_inactive_invite_returns_400(self):
        invite = CampaignInvite.objects.create(
            campaign=self.campaign,
            invited_by=self.dm,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=False,
        )
        self.authenticate(self.outsider)

        response = self.client.post(
            reverse("campaign-invite-accept", kwargs={"token": invite.token})
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invite expired")

    def test_invalid_token_returns_404(self):
        self.authenticate(self.outsider)

        response = self.client.post(
            "/api/campaigns/invites/00000000-0000-0000-0000-000000000000/accept/"
        )

        self.assertEqual(response.status_code, 404)
