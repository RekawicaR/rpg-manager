from apps.campaigns.models import CampaignSource
from apps.campaigns.tests.base import CampaignAPITestCase
from apps.compendium.models.source import Source


class CampaignSourceTests(CampaignAPITestCase):
    def setUp(self):
        self.dm = self.create_user("dm")
        self.player = self.create_user("player")
        self.outsider = self.create_user("outsider")
        self.campaign = self.create_campaign_with_members(self.dm, [self.player])
        self.source1 = Source.objects.create(code="PHB", name="Players Handbook")
        self.source2 = Source.objects.create(code="DMG", name="Dungeon Masters Guide")
        self.url = f"/api/campaigns/{self.campaign.id}/sources/"

    def test_dm_can_update_sources(self):
        self.authenticate(self.dm)

        response = self.client.put(
            self.url,
            {"source_ids": [self.source1.id, self.source2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(self.campaign.sources.values_list("id", flat=True)),
            {self.source1.id, self.source2.id},
        )

    def test_dm_can_clear_sources(self):
        CampaignSource.objects.bulk_create([
            CampaignSource(campaign=self.campaign, source=self.source1),
            CampaignSource(campaign=self.campaign, source=self.source2),
        ])
        self.authenticate(self.dm)

        response = self.client.put(
            self.url,
            {"source_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.campaign.sources.count(), 0)

    def test_player_cannot_update_sources(self):
        self.authenticate(self.player)

        response = self.client.put(
            self.url,
            {"source_ids": [self.source1.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.campaign.sources.count(), 0)

    def test_member_can_get_sources(self):
        CampaignSource.objects.create(campaign=self.campaign, source=self.source1)
        self.authenticate(self.player)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.source1.id)

    def test_non_member_cannot_get_sources(self):
        self.authenticate(self.outsider)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_duplicate_sources_are_rejected(self):
        self.authenticate(self.dm)

        response = self.client.put(
            self.url,
            {"source_ids": [self.source1.id, self.source1.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_source_id_is_rejected(self):
        self.authenticate(self.dm)

        response = self.client.put(
            self.url,
            {"source_ids": [9999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
