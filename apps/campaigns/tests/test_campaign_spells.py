from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from apps.campaigns.tests.base import CampaignAPITestCase
from apps.compendium.models.spell import Spell
from apps.compendium.models.character_class import CharacterClass
from apps.campaigns.models import CampaignItemRule, Source


class CampaignSpellListTests(CampaignAPITestCase):

    def setUp(self):
        self.dm = self.create_user("dm")
        self.player = self.create_user("player")
        self.outsider = self.create_user("outsider")

        self.campaign = self.create_campaign_with_members(
            self.dm,
            [self.player]
        )

        self.spell_url = reverse(
            "campaign-spells",
            kwargs={"campaign_id": self.campaign.id}
        )
        self.rules_url = reverse(
            "campaign-rules",
            kwargs={"campaign_id": self.campaign.id}
        )

        self.source_allowed = Source.objects.create(
            code="PHB",
            name="Player's Handbook"
        )
        self.source_blocked = Source.objects.create(
            code="XGE",
            name="Xanathar's Guide"
        )

        self.campaign.sources.add(self.source_allowed)

        self.wizard = CharacterClass.objects.create(
            name="Wizard",
            source=self.source_allowed,
        )

        self.spell_allowed = Spell.objects.create(
            name="Fireball",
            source=self.source_allowed,
            spell_level=3,
            casting_type=Spell.CastingType.ACTION,
            range_type=Spell.RangeType.DISTANCE,
            range_value=150,
            range_unit="FT",
            duration_type=Spell.DurationType.INSTANT,
            concentration=False,
            ritual=False,
            verbal_component=True,
            somatic_component=True,
            material_component="A tiny ball of bat guano and sulfur",
            school="EVOC",
            description="A bright streak flashes.",
        )
        self.spell_allowed.classes.add(self.wizard)

        self.spell_not_allowed = Spell.objects.create(
            name="Weird Spell",
            source=self.source_blocked,
            spell_level=3,
            casting_type=Spell.CastingType.ACTION,
            range_type=Spell.RangeType.DISTANCE,
            range_value=150,
            range_unit="FT",
            duration_type=Spell.DurationType.INSTANT,
            concentration=False,
            ritual=False,
            verbal_component=True,
            somatic_component=True,
            material_component="A tiny ball of bat guano and sulfur",
            school="EVOC",
            description="Weird stuff...",
        )
        self.spell_not_allowed.classes.add(self.wizard)

        self.ct = ContentType.objects.get_for_model(Spell)

    def test_member_can_list_spells(self):
        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_access(self):
        self.authenticate(self.outsider)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_access(self):
        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 401)

    def test_spell_from_allowed_source_is_visible(self):
        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            self.spell_allowed.id
        )

    def test_spell_from_not_allowed_source_is_hidden(self):
        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(self.spell_not_allowed.id, ids)

    def test_block_rule_hides_spell(self):
        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_allowed.id,
            rule_type="BLOCK"
        )

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_allow_rule_works_with_item_from_blocked_source(self):
        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_not_allowed.id,
            rule_type="ALLOW"
        )

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.spell_not_allowed.id, ids)

    def test_allow_overrides_block(self):
        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_allowed.id,
            rule_type="BLOCK"
        )

        self.authenticate(self.dm)

        response = self.client.post(
            self.rules_url,
            {
                "content_type": "spell",
                "object_id": self.spell_allowed.id,
                "rule_type": "ALLOW",
            },
            format="json",
        )

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.spell_allowed.id, ids)

    def test_delete_allow_works(self):
        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_not_allowed.id,
            rule_type="ALLOW"
        )

        self.authenticate(self.dm)

        response = self.client.delete(
            reverse(
                "campaign-rule-delete",
                kwargs={"campaign_id": self.campaign.id, "rule_id": rule.id}
            )
        )
        self.assertEqual(response.status_code, 204)

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(self.spell_not_allowed.id, ids)

    def test_delete_block_works(self):
        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_allowed.id,
            rule_type="BLOCK"
        )

        self.authenticate(self.dm)

        response = self.client.delete(
            reverse(
                "campaign-rule-delete",
                kwargs={"campaign_id": self.campaign.id, "rule_id": rule.id}
            )
        )
        self.assertEqual(response.status_code, 204)

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.spell_allowed.id, ids)

    def test_no_sources_only_allow_works(self):
        self.campaign.sources.clear()

        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell_not_allowed.id,
            rule_type="ALLOW"
        )

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            self.spell_not_allowed.id
        )

    def test_no_sources_no_rules_returns_empty(self):
        self.campaign.sources.clear()

        self.authenticate(self.player)

        response = self.client.get(self.spell_url)

        self.assertEqual(response.data["count"], 0)
