from django.core.exceptions import ValidationError as CoreValidationError
from rest_framework import serializers
from apps.compendium.models.spell import Spell, validate_spell_rules
from apps.compendium.models.character_class import CharacterClass


SPELL_DETAIL_FIELDS = [
    "id",
    "name",
    "source",
    "spell_level",
    "casting_type",
    "casting_value",
    "casting_unit",
    "range_type",
    "range_value",
    "range_unit",
    "range_area_type",
    "range_area_value",
    "range_area_unit",
    "duration_type",
    "duration_value",
    "duration_unit",
    "concentration",
    "ritual",
    "verbal_component",
    "somatic_component",
    "material_component",
    "school",
    "description",
    "classes",
]


class SpellWriteSerializer(serializers.ModelSerializer):

    # TODO: Later will probably use Character Serializer
    classes = serializers.PrimaryKeyRelatedField(
        queryset=CharacterClass.objects.all(),
        many=True
    )

    class Meta:
        model = Spell
        fields = SPELL_DETAIL_FIELDS

    def validate(self, data):
        instance = getattr(self, "instance", None)

        merged_data = {
            "casting_type": data.get("casting_type", getattr(instance, "casting_type", None)),
            "casting_value": data.get("casting_value", getattr(instance, "casting_value", None)),
            "casting_unit": data.get("casting_unit", getattr(instance, "casting_unit", None)),
            "duration_type": data.get("duration_type", getattr(instance, "duration_type", None)),
            "duration_value": data.get("duration_value", getattr(instance, "duration_value", None)),
            "duration_unit": data.get("duration_unit", getattr(instance, "duration_unit", None)),
            "range_type": data.get("range_type", getattr(instance, "range_type", None)),
            "range_value": data.get("range_value", getattr(instance, "range_value", None)),
            "range_unit": data.get("range_unit", getattr(instance, "range_unit", None)),
            "range_area_type": data.get("range_area_type", getattr(instance, "range_area_type", None)),
            "range_area_value": data.get("range_area_value", getattr(instance, "range_area_value", None)),
            "range_area_unit": data.get("range_area_unit", getattr(instance, "range_area_unit", None)),
            "concentration": data.get("concentration", getattr(instance, "concentration", None)),
            "classes": data.get(
                "classes",
                list(instance.classes.all()) if instance else []
            ),
        }

        try:
            validate_spell_rules(merged_data)
        except CoreValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return data


class SpellListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spell
        fields = [
            "id",
            "name",
            "spell_level",
            "concentration",
            "ritual",
        ]


class SpellDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spell
        fields = SPELL_DETAIL_FIELDS
