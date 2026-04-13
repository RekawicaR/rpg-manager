from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.compendium.serializers.spell import SpellListSerializer, SpellDetailSerializer, SpellWriteSerializer
from apps.compendium.models.spell import Spell
from apps.accounts.permissions import IsModerator


class SpellPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SpellViewSet(ModelViewSet):
    queryset = Spell.objects.select_related(
        "source").prefetch_related("classes")
    pagination_class = SpellPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "spell_level", "school"]
    ordering = ["name"]

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
