from django.core.exceptions import ValidationError as CoreValidationError
from rest_framework import serializers
from apps.compendium.models.spell import Spell
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
        instance = self.instance or self.Meta.model()
        m2m_fields = {
            field.name for field in self.Meta.model._meta.many_to_many
        }

        for attr, value in data.items():
            if attr in m2m_fields:
                continue
            setattr(instance, attr, value)

        try:
            instance.full_clean()
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
