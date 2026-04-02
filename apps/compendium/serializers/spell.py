from rest_framework import serializers
from apps.compendium.models.spell import Spell
from apps.compendium.models.character_class import CharacterClass


class SpellWriteSerializer(serializers.ModelSerializer):

    # TODO: Later will probably use Character Serializer
    classes = serializers.PrimaryKeyRelatedField(
        queryset=CharacterClass.objects.all(),
        many=True
    )

    class Meta:
        model = Spell
        fields = [
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

    # TODO: review it
    def validate(self, data):
        instance = getattr(self, "instance", Spell())

        for field, value in data.items():
            if field != "classes":
                setattr(instance, field, value)

        instance.full_clean()
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
        fields = [
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
