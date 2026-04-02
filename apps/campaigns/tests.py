from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from apps.campaigns.models import Campaign, CampaignMembership, CampaignInvite, CampaignSource, CampaignItemRule
from apps.compendium.models.source import Source
from apps.compendium.models.spell import Spell


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


class CampaignDetailTests(APITestCase):

    def setUp(self):
        self.dm = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="Test1Password123"
        )

        self.player = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="Test2Password123"
        )

        self.campaign = Campaign.objects.create(
            name="Test",
            description="desc",
            created_by=self.dm
        )

        CampaignMembership.objects.create(
            user=self.dm,
            campaign=self.campaign,
            role="DM"
        )

        CampaignMembership.objects.create(
            user=self.player,
            campaign=self.campaign,
            role="PLAYER"
        )

    def test_player_can_get_campaign(self):

        self.client.force_authenticate(user=self.player)

        response = self.client.get(
            f"/api/campaigns/{self.campaign.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.campaign.id)
        self.assertEqual(response.data["name"], self.campaign.name)
        self.assertEqual(
            response.data["description"], self.campaign.description)

    def test_dm_can_update_campaign(self):

        self.client.force_authenticate(user=self.dm)

        response = self.client.patch(
            f"/api/campaigns/{self.campaign.id}/",
            {"name": "Updated"}
        )

        self.assertEqual(response.status_code, 200)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.name, "Updated")

    def test_player_cannot_update_campaign(self):

        self.client.force_authenticate(user=self.player)

        response = self.client.patch(
            f"/api/campaigns/{self.campaign.id}/",
            {"name": "Hacked"}
        )

        self.assertEqual(response.status_code, 403)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.name, "Test")

    def test_player_cannot_delete_campaign(self):

        self.client.force_authenticate(user=self.player)

        response = self.client.delete(
            f"/api/campaigns/{self.campaign.id}/"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Campaign.objects.count(), 1)

    def test_dm_can_delete_campaign(self):

        self.client.force_authenticate(user=self.dm)

        response = self.client.delete(
            f"/api/campaigns/{self.campaign.id}/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Campaign.objects.count(), 0)


class CampaignSourceTests(APITestCase):

    def setUp(self):

        self.dm = User.objects.create_user(username="dm", password="pass")
        self.player = User.objects.create_user(
            username="player", password="pass")

        self.campaign = Campaign.objects.create(
            name="Test",
            description="desc",
            created_by=self.dm
        )

        CampaignMembership.objects.create(
            user=self.dm,
            campaign=self.campaign,
            role="DM"
        )

        CampaignMembership.objects.create(
            user=self.player,
            campaign=self.campaign,
            role="PLAYER"
        )

        self.source1 = Source.objects.create(
            code="PHB", name="Players Handbook")
        self.source2 = Source.objects.create(
            code="DMG", name="Dungeon Masters Guide")

    def test_dm_can_update_sources(self):

        self.client.force_authenticate(user=self.dm)

        response = self.client.put(
            f"/api/campaigns/{self.campaign.id}/sources/",
            {"source_ids": [self.source1.id, self.source2.id]},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(self.campaign.sources.values_list('id', flat=True)),
            {self.source1.id, self.source2.id}
        )

    def test_dm_can_clear_sources(self):
        CampaignSource.objects.bulk_create([
            CampaignSource(campaign=self.campaign, source=self.source1),
            CampaignSource(campaign=self.campaign, source=self.source2),
        ])

        self.client.force_authenticate(user=self.dm)
        response = self.client.put(
            f"/api/campaigns/{self.campaign.id}/sources/",
            {"source_ids": []},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.campaign.sources.count(), 0)

    def test_player_cannot_update_sources(self):

        self.client.force_authenticate(user=self.player)

        response = self.client.put(
            f"/api/campaigns/{self.campaign.id}/sources/",
            {"source_ids": [self.source1.id]},
            format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.campaign.sources.count(), 0)

    def test_member_can_get_sources(self):

        CampaignSource.objects.create(
            campaign=self.campaign,
            source=self.source1
        )

        self.client.force_authenticate(user=self.player)

        response = self.client.get(
            f"/api/campaigns/{self.campaign.id}/sources/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.source1.id)

    def test_dm_can_get_sources(self):
        CampaignSource.objects.create(
            campaign=self.campaign, source=self.source2)

        self.client.force_authenticate(user=self.dm)
        response = self.client.get(
            f"/api/campaigns/{self.campaign.id}/sources/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.source2.id)

    def test_non_member_cannot_get_sources(self):
        outsider = User.objects.create_user(
            username="outsider", password="pass")
        self.client.force_authenticate(user=outsider)

        response = self.client.get(
            f"/api/campaigns/{self.campaign.id}/sources/")
        self.assertEqual(response.status_code, 403)


class CampaignItemRuleTests(APITestCase):

    def setUp(self):

        self.dm = User.objects.create_user(username="dm", password="pass")
        self.player = User.objects.create_user(
            username="player",
            password="pass"
        )
        self.outsider = User.objects.create_user(
            username="outsider",
            password="pass"
        )

        self.campaign = Campaign.objects.create(
            name="Test",
            description="desc",
            created_by=self.dm
        )

        CampaignMembership.objects.create(
            user=self.dm,
            campaign=self.campaign,
            role="DM"
        )

        CampaignMembership.objects.create(
            user=self.player,
            campaign=self.campaign,
            role="PLAYER"
        )

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
            description="Boom"
        )

        self.ct = ContentType.objects.get_for_model(Spell)

    def test_create_rule_as_dm(self):

        self.client.force_authenticate(self.dm)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        data = {
            "content_type": "spell",
            "object_id": self.spell.id,
            "rule_type": "ALLOW"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignItemRule.objects.count(), 1)

        rule = CampaignItemRule.objects.first()
        self.assertEqual(rule.rule_type, "ALLOW")

    def test_create_rule_as_player_forbidden(self):

        self.client.force_authenticate(self.player)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        data = {
            "content_type": "spell",
            "object_id": self.spell.id,
            "rule_type": "ALLOW"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_invalid_content_type(self):

        self.client.force_authenticate(self.dm)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        data = {
            "content_type": "invalid",
            "object_id": self.spell.id,
            "rule_type": "ALLOW"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_non_existing_object(self):

        self.client.force_authenticate(self.dm)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        data = {
            "content_type": "spell",
            "object_id": 9999,
            "rule_type": "ALLOW"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_create_rule_updates_existing(self):

        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell.id,
            rule_type="BLOCK"
        )

        self.client.force_authenticate(self.dm)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        data = {
            "content_type": "spell",
            "object_id": self.spell.id,
            "rule_type": "ALLOW"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CampaignItemRule.objects.count(), 1)

        rule = CampaignItemRule.objects.first()
        self.assertEqual(rule.rule_type, "ALLOW")

    def test_list_rules_as_member(self):

        CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell.id,
            rule_type="ALLOW"
        )

        self.client.force_authenticate(self.player)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_rules_as_outsider_forbidden(self):

        self.client.force_authenticate(self.outsider)

        url = f"/api/campaigns/{self.campaign.id}/rules/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_delete_rule_as_dm(self):

        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell.id,
            rule_type="ALLOW"
        )

        self.client.force_authenticate(self.dm)

        url = f"/api/campaigns/{self.campaign.id}/rules/{rule.id}/"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(CampaignItemRule.objects.count(), 0)

    def test_delete_rule_as_player_forbidden(self):

        rule = CampaignItemRule.objects.create(
            campaign=self.campaign,
            content_type=self.ct,
            object_id=self.spell.id,
            rule_type="ALLOW"
        )

        self.client.force_authenticate(self.player)

        url = f"/api/campaigns/{self.campaign.id}/rules/{rule.id}/"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
