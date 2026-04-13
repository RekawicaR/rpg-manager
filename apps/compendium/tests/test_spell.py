from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.compendium.models.character_class import CharacterClass
from apps.compendium.models.source import Source
from apps.compendium.models.spell import Spell


User = get_user_model()


class SpellAPITests(APITestCase):
    def setUp(self):
        self.source = Source.objects.create(
            code="PHB",
            name="Player's Handbook"
        )
        self.alt_source = Source.objects.create(
            code="XGE",
            name="Xanathar's Guide"
        )

        self.wizard = CharacterClass.objects.create(
            name="Wizard",
            source=self.source,
        )
        self.cleric = CharacterClass.objects.create(
            name="Cleric",
            source=self.source,
        )

        self.user = User.objects.create_user(
            username="user",
            password="TestPassword123",
            role=User.GlobalRole.USER,
        )
        self.moderator = User.objects.create_user(
            username="moderator",
            password="TestPassword123",
            role=User.GlobalRole.MODERATOR,
        )

        self.spell = Spell.objects.create(
            name="Fireball",
            source=self.source,
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
        self.spell.classes.add(self.wizard)

        self.list_url = reverse("spells-list")
        self.detail_url = reverse(
            "spells-detail", kwargs={"pk": self.spell.pk}
        )

    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

    def default_payload(self):
        return {
            "name": "Bless",
            "source": self.source.id,
            "spell_level": 1,
            "casting_type": Spell.CastingType.ACTION,
            "casting_value": None,
            "casting_unit": None,
            "range_type": Spell.RangeType.DISTANCE,
            "range_value": 30,
            "range_unit": "FT",
            "range_area_type": None,
            "range_area_value": None,
            "range_area_unit": None,
            "duration_type": Spell.DurationType.TIME,
            "duration_value": 1,
            "duration_unit": "MINUTE",
            "concentration": True,
            "ritual": False,
            "verbal_component": True,
            "somatic_component": True,
            "material_component": "A sprinkling of holy water",
            "school": "ENCH",
            "description": "You bless up to three creatures.",
            "classes": [self.cleric.id],
        }

    def test_list_spells_is_public(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.spell.id)
        self.assertIn("name", response.data["results"][0])
        self.assertNotIn("source", response.data["results"][0])
        self.assertNotIn("description", response.data["results"][0])

    def test_list_spells_is_paginated(self):
        for index in range(25):
            spell = Spell.objects.create(
                name=f"Spell {index:02d}",
                source=self.source,
                spell_level=1,
                casting_type=Spell.CastingType.ACTION,
                range_type=Spell.RangeType.DISTANCE,
                range_value=30,
                range_unit="FT",
                duration_type=Spell.DurationType.INSTANT,
                concentration=False,
                ritual=False,
                verbal_component=True,
                somatic_component=False,
                material_component="",
                school="ABJ",
                description="Test spell",
            )
            spell.classes.add(self.wizard)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 26)  # 25 created + 1 existing
        self.assertEqual(len(response.data["results"]), 20)  # page limit
        self.assertIsNotNone(response.data["next"])

    def test_list_spells_supports_search(self):
        other_spell = Spell.objects.create(
            name="Bless",
            source=self.source,
            spell_level=1,
            casting_type=Spell.CastingType.ACTION,
            range_type=Spell.RangeType.DISTANCE,
            range_value=30,
            range_unit="FT",
            duration_type=Spell.DurationType.TIME,
            duration_value=1,
            duration_unit="MINUTE",
            concentration=True,
            ritual=False,
            verbal_component=True,
            somatic_component=True,
            material_component="A sprinkling of holy water",
            school="ENCH",
            description="You bless up to three creatures.",
        )
        other_spell.classes.add(self.cleric)

        response = self.client.get(self.list_url, {"search": "fire"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Fireball")

    def test_list_spells_supports_ordering(self):
        lower_level_spell = Spell.objects.create(
            name="Bless",
            source=self.source,
            spell_level=1,
            casting_type=Spell.CastingType.ACTION,
            range_type=Spell.RangeType.DISTANCE,
            range_value=30,
            range_unit="FT",
            duration_type=Spell.DurationType.TIME,
            duration_value=1,
            duration_unit="MINUTE",
            concentration=True,
            ritual=False,
            verbal_component=True,
            somatic_component=True,
            material_component="A sprinkling of holy water",
            school="ENCH",
            description="You bless up to three creatures.",
        )
        lower_level_spell.classes.add(self.cleric)

        response = self.client.get(self.list_url, {"ordering": "-spell_level"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["name"], "Fireball")

    def test_retrieve_spell_is_public_and_uses_detail_serializer(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.spell.id)
        self.assertEqual(response.data["source"], self.source.id)
        self.assertEqual(response.data["classes"], [self.wizard.id])
        self.assertIn("description", response.data)
        self.assertIn("material_component", response.data)

    def test_anonymous_user_cannot_create_spell(self):
        response = self.client.post(
            self.list_url, self.default_payload(), format="json")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Spell.objects.count(), 1)

    def test_non_moderator_cannot_create_spell(self):
        self.authenticate(self.user)

        response = self.client.post(
            self.list_url, self.default_payload(), format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Spell.objects.count(), 1)

    def test_moderator_can_create_spell(self):
        self.authenticate(self.moderator)

        response = self.client.post(
            self.list_url, self.default_payload(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Spell.objects.count(), 2)
        created_spell = Spell.objects.get(name="Bless")
        self.assertEqual(created_spell.source, self.source)
        self.assertEqual(list(created_spell.classes.values_list(
            "id", flat=True)), [self.cleric.id])
        self.assertEqual(response.data["classes"], [self.cleric.id])

    def test_non_moderator_cannot_update_spell(self):
        self.authenticate(self.user)

        response = self.client.patch(
            self.detail_url,
            {"name": "Hacked"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.spell.refresh_from_db()
        self.assertEqual(self.spell.name, "Fireball")

    def test_moderator_can_patch_spell(self):
        self.authenticate(self.moderator)

        response = self.client.patch(
            self.detail_url,
            {
                "name": "Chain Lightning",
                "source": self.alt_source.id,
                "classes": [self.wizard.id, self.cleric.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.spell.refresh_from_db()
        self.assertEqual(self.spell.name, "Chain Lightning")
        self.assertEqual(self.spell.source, self.alt_source)
        self.assertEqual(
            set(self.spell.classes.values_list("id", flat=True)),
            {self.wizard.id, self.cleric.id},
        )

    def test_non_moderator_cannot_delete_spell(self):
        self.authenticate(self.user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Spell.objects.filter(id=self.spell.id).exists())

    def test_moderator_can_delete_spell(self):
        self.authenticate(self.moderator)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Spell.objects.filter(id=self.spell.id).exists())

    def test_create_spell_rejects_time_casting_without_required_fields(self):
        self.authenticate(self.moderator)
        payload = self.default_payload()
        payload.update(
            {
                "casting_type": Spell.CastingType.TIME,
                "casting_value": None,
                "casting_unit": None,
            }
        )

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["casting_value"][0], "Required when casting_type is TIME")
        self.assertEqual(response.data["casting_unit"]
                         [0], "Required when casting_type is TIME")

    def test_create_spell_rejects_distance_range_without_required_fields(self):
        self.authenticate(self.moderator)
        payload = self.default_payload()
        payload.update(
            {
                "range_type": Spell.RangeType.DISTANCE,
                "range_value": None,
                "range_unit": None,
            }
        )

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["range_value"]
                         [0], "Required when range_type is DISTANCE")
        self.assertEqual(response.data["range_unit"]
                         [0], "Required when range_type is DISTANCE")

    def test_create_spell_rejects_area_without_value_and_unit(self):
        self.authenticate(self.moderator)
        payload = self.default_payload()
        payload.update(
            {
                "range_area_type": "CONE",
                "range_area_value": None,
                "range_area_unit": None,
            }
        )

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["range_area_value"][0], "Required when range_area_type is set")
        self.assertEqual(
            response.data["range_area_unit"][0], "Required when range_area_type is set")

    def test_create_spell_rejects_concentration_for_instant_duration(self):
        self.authenticate(self.moderator)
        payload = self.default_payload()
        payload.update(
            {
                "duration_type": Spell.DurationType.INSTANT,
                "duration_value": None,
                "duration_unit": None,
                "concentration": True,
            }
        )

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["concentration"][0], "Instant spells cannot require concentration")

    def test_partial_update_uses_existing_values_for_validation(self):
        self.authenticate(self.moderator)

        response = self.client.patch(
            self.detail_url,
            {"concentration": True},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["concentration"][0], "Instant spells cannot require concentration")

    def test_partial_update_rejects_update_without_required_fields(self):
        self.authenticate(self.moderator)

        response = self.client.patch(
            self.detail_url,
            {"duration_type": Spell.DurationType.TIME},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["duration_value"][0], "Required when duration_type is TIME")
        self.assertEqual(
            response.data["duration_unit"][0], "Required when duration_type is TIME")
