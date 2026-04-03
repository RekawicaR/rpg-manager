from django.urls import reverse

from apps.campaigns.models import Campaign, CampaignMembership
from apps.campaigns.tests.base import CampaignAPITestCase


class CampaignCRUDTests(CampaignAPITestCase):
    def setUp(self):
        self.dm = self.create_user("dm")
        self.player = self.create_user("player")
        self.outsider = self.create_user("outsider")
        self.campaign = self.create_campaign_with_members(self.dm, [self.player])

    def test_create_campaign_sets_creator_as_dm(self):
        self.authenticate(self.dm)

        response = self.client.post(
            reverse("campaigns-list"),
            {"name": "My Campaign", "description": "Test campaign"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created_campaign = Campaign.objects.get(id=response.data["id"])
        self.assertEqual(created_campaign.created_by, self.dm)
        self.assertTrue(
            CampaignMembership.objects.filter(
                user=self.dm,
                campaign=created_campaign,
                role=CampaignMembership.Role.DM,
            ).exists()
        )

    def test_list_returns_only_user_campaigns(self):
        other_dm = self.create_user("other-dm")
        self.create_campaign_with_members(other_dm)
        self.authenticate(self.player)

        response = self.client.get(reverse("campaigns-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.campaign.id)

    def test_player_can_get_campaign_detail(self):
        self.authenticate(self.player)

        response = self.client.get(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.campaign.id)
        self.assertEqual(response.data["name"], self.campaign.name)

    def test_outsider_cannot_get_campaign_detail(self):
        self.authenticate(self.outsider)

        response = self.client.get(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_dm_can_update_campaign(self):
        self.authenticate(self.dm)

        response = self.client.patch(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id}),
            {"name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.name, "Updated")

    def test_player_cannot_update_campaign(self):
        self.authenticate(self.player)

        response = self.client.patch(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id}),
            {"name": "Hacked"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.name, "Test Campaign")

    def test_dm_can_delete_campaign(self):
        self.authenticate(self.dm)

        response = self.client.delete(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id})
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Campaign.objects.filter(id=self.campaign.id).exists())

    def test_player_cannot_delete_campaign(self):
        self.authenticate(self.player)

        response = self.client.delete(
            reverse("campaigns-detail", kwargs={"pk": self.campaign.id})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Campaign.objects.filter(id=self.campaign.id).exists())
