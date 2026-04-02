from django.db import models
from django.core.exceptions import ValidationError
from apps.compendium.models.base_compendium_item import BaseCompendiumItem
from apps.compendium.choices import TimeUnit, MagicSchool, DistanceUnit, AreaType


class Spell(BaseCompendiumItem):

    class SpellLevel(models.IntegerChoices):
        CANTRIP = 0, "Cantrip"
        LEVEL_1 = 1, "1"
        LEVEL_2 = 2, "2"
        LEVEL_3 = 3, "3"
        LEVEL_4 = 4, "4"
        LEVEL_5 = 5, "5"
        LEVEL_6 = 6, "6"
        LEVEL_7 = 7, "7"
        LEVEL_8 = 8, "8"
        LEVEL_9 = 9, "9"

    class CastingType(models.TextChoices):
        ACTION = "ACTION", "Action"
        BONUS_ACTION = "BONUS_ACTION", "Bonus Action"
        REACTION = "REACTION", "Reaction"
        TIME = "TIME", "Time-based"
        SPECIAL = "SPECIAL", "Special"

    class RangeType(models.TextChoices):
        SELF = "SELF", "Self"
        TOUCH = "TOUCH", "Touch"
        DISTANCE = "DISTANCE", "Distance"
        SPECIAL = "SPECIAL", "Special"

    class DurationType(models.TextChoices):
        INSTANT = "INSTANT", "Instant"
        ROUND = "ROUND", "Round"
        TIME = "TIME", "Time-based"
        SPECIAL = "SPECIAL", "Special"

    spell_level = models.IntegerField(choices=SpellLevel.choices)

    # ------- How long to cast the spell -------
    casting_type = models.CharField(
        max_length=20,
        choices=CastingType.choices
    )
    # only relevant for casting_type == TIME
    casting_value = models.IntegerField(null=True, blank=True)
    casting_unit = models.CharField(
        max_length=20,
        choices=TimeUnit.choices,
        null=True,
        blank=True
    )

    # ------- Range of spell -------
    range_type = models.CharField(max_length=20, choices=RangeType.choices)
    # only relevant for range_type == DISTANCE
    range_value = models.IntegerField(null=True, blank=True)
    range_unit = models.CharField(
        max_length=10,
        choices=DistanceUnit.choices,
        null=True,
        blank=True
    )
    # optional if there is an area effect
    range_area_type = models.CharField(
        max_length=10,
        choices=AreaType.choices,
        null=True,
        blank=True
    )
    range_area_value = models.IntegerField(null=True, blank=True)
    range_area_unit = models.CharField(
        max_length=10,
        choices=DistanceUnit.choices,
        null=True,
        blank=True
    )

    # ------- How long the spell lasts -------
    duration_type = models.CharField(
        max_length=20,
        choices=DurationType.choices
    )
    # only relevant for duration_type == TIME
    duration_value = models.IntegerField(null=True, blank=True)
    duration_unit = models.CharField(
        max_length=20,
        choices=TimeUnit.choices,
        null=True,
        blank=True
    )

    # ------- Spell labels -------
    concentration = models.BooleanField(default=False)
    ritual = models.BooleanField(default=False)

    # ------- Spell components -------
    verbal_component = models.BooleanField(default=False)
    somatic_component = models.BooleanField(default=False)
    material_component = models.TextField(blank=True)

    # ------- School of magic -------
    school = models.CharField(max_length=10, choices=MagicSchool.choices)

    # ------- Full spell description -------
    description = models.TextField()

    # ------- List of character classes that have access to this spell -------
    classes = models.ManyToManyField(
        "CharacterClass",
        related_name="spells"
    )

    def clean(self):
        errors = {}

        # -------- CASTING --------
        if self.casting_type == self.CastingType.TIME:
            if self.casting_value is None:
                errors["casting_value"] = "Required when casting_type is TIME"
            if self.casting_unit is None:
                errors["casting_unit"] = "Required when casting_type is TIME"
        else:
            if self.casting_value is not None:
                errors["casting_value"] = "Only allowed when casting_type is TIME"
            if self.casting_unit is not None:
                errors["casting_unit"] = "Only allowed when casting_type is TIME"

        # -------- DURATION --------
        if self.duration_type == self.DurationType.TIME:
            if self.duration_value is None:
                errors["duration_value"] = "Required when duration_type is TIME"
            if self.duration_unit is None:
                errors["duration_unit"] = "Required when duration_type is TIME"
        else:
            if self.duration_value is not None:
                errors["duration_value"] = "Only allowed when duration_type is TIME"
            if self.duration_unit is not None:
                errors["duration_unit"] = "Only allowed when duration_type is TIME"

        # -------- RANGE (DISTANCE) --------
        if self.range_type == self.RangeType.DISTANCE:
            if self.range_value is None:
                errors["range_value"] = "Required when range_type is DISTANCE"
            if self.range_unit is None:
                errors["range_unit"] = "Required when range_type is DISTANCE"
        else:
            if self.range_value is not None:
                errors["range_value"] = "Only allowed when range_type is DISTANCE"
            if self.range_unit is not None:
                errors["range_unit"] = "Only allowed when range_type is DISTANCE"

        # -------- AREA --------
        if self.range_area_type:
            if self.range_area_value is None:
                errors["range_area_value"] = "Required when range_area_type is set"
            if self.range_area_unit is None:
                errors["range_area_unit"] = "Required when range_area_type is set"
        else:
            if self.range_area_value is not None:
                errors["range_area_value"] = "Only allowed when range_area_type is set"
            if self.range_area_unit is not None:
                errors["range_area_unit"] = "Only allowed when range_area_type is set"

        # -------- LOGICAL VALIDATIONS --------

        # concentration makes no sense for instant spells
        if self.duration_type == self.DurationType.INSTANT and self.concentration:
            errors["concentration"] = "Instant spells cannot require concentration"

        # -------- FINAL --------
        if errors:
            raise ValidationError(errors)
