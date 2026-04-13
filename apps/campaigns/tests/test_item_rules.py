from django.contrib.contenttypes.models import ContentType
from apps.campaigns.models import CampaignItemRule
from apps.campaigns.tests.base import CampaignAPITestCase
from apps.compendium.models.source import Source
from apps.compendium.models.spell import Spell


class CampaignItemRuleTests(CampaignAPITestCase):
    def setUp(self):
        self.dm = self.create_user("dm")
        self.player = self.create_user("player")
        self.outsider = self.create_user("outsider")
        self.campaign = self.create_campaign_with_members(
            self.dm, [self.player])
        self.source = Source.objects.create(
            code="PHB", name="Players Handbook")
        self.spell = Spell.objects.create(
            name="Fireball",
            source=self.source,
            spell_level=3,
            casting_type="ACTION",
            range_type="DISTANCE",
            range_value=60,
            range_unit="FT",
            duration_type="INSTANT",
            school="EVOC",
            description="Boom",
        )
        self.content_type = ContentType.objects.get_for_model(Spell)
        self.list_url = f"/api/campaigns/{self.campaign.id}/rules/"

    def test_create_rule_as_dm(self):
        self.authenticate(self.dm)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": self.spell.id,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignItemRule.objects.count(), 1)
        self.assertEqual(response.data["content_type"], "spell")
        self.assertEqual(response.data["rule_type"], "ALLOW")

    def test_player_cannot_create_rule(self):
        self.authenticate(self.player)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": self.spell.id,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_outsider_cannot_create_rule(self):
        self.authenticate(self.outsider)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": self.spell.id,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_invalid_content_type(self):
        self.authenticate(self.dm)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "invalid",
                "object_id": self.spell.id,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_invalid_object_id(self):
        self.authenticate(self.dm)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": 9999,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_invalid_rule_type(self):
        self.authenticate(self.dm)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": self.spell.id,
                "rule_type": "INVALID",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_updates_existing_rule(self):
        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.content_type,
            object_id=self.spell.id,
            rule_type="ALLOW",
        )
        self.authenticate(self.dm)

        response = self.client.post(
            self.list_url,
            {
                "content_type": "spell",
                "object_id": self.spell.id,
                "rule_type": "BLOCK",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignItemRule.objects.count(), 1)
        self.assertEqual(CampaignItemRule.objects.first().rule_type, "BLOCK")

    def test_member_can_list_rules(self):
        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.content_type,
            object_id=self.spell.id,
            rule_type="ALLOW",
        )
        self.authenticate(self.player)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_outsider_cannot_list_rules(self):
        self.authenticate(self.outsider)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 403)

    def test_dm_can_delete_rule(self):
        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.content_type,
            object_id=self.spell.id,
            rule_type="ALLOW",
        )
        self.authenticate(self.dm)

        response = self.client.delete(
            f"/api/campaigns/{self.campaign.id}/rules/{rule.id}/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(CampaignItemRule.objects.filter(id=rule.id).exists())

    def test_player_cannot_delete_rule(self):
        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.content_type,
            object_id=self.spell.id,
            rule_type="ALLOW",
        )
        self.authenticate(self.player)

        response = self.client.delete(
            f"/api/campaigns/{self.campaign.id}/rules/{rule.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_delete_rule(self):
        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.content_type,
            object_id=self.spell.id,
            rule_type="ALLOW",
        )
        self.authenticate(self.outsider)

        response = self.client.delete(
            f"/api/campaigns/{self.campaign.id}/rules/{rule.id}/"
        )

        self.assertEqual(response.status_code, 403)
