from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.compendium.serializers.spell import SpellListSerializer, SpellDetailSerializer, SpellWriteSerializer
from apps.compendium.models.spell import Spell
from apps.accounts.permissions import IsModerator


class SpellViewSet(ModelViewSet):
    queryset = Spell.objects.all()

    def get_serializer_class(self):

        if self.action == "list":
            return SpellListSerializer

        if self.action == "retrieve":
            return SpellDetailSerializer

        return SpellWriteSerializer

    def get_permissions(self):

        if self.action in ["list", "retrieve"]:
            return [AllowAny()]

        return [IsAuthenticated(), IsModerator()]
