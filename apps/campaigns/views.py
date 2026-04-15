from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .permissions import IsCampaignDM, IsCampaignMember
from .models import Campaign, CampaignMembership, CampaignInvite, CampaignItemRule
from .serializers import CampaignSerializer, CampaignSourceUpdateSerializer, CampaignItemRuleCreateSerializer, CampaignItemRuleSerializer
from apps.compendium.serializers.source import SourceSerializer
from apps.compendium.serializers.spell import SpellListSerializer
from apps.compendium.models.spell import Spell
from apps.compendium.views.spell import SpellViewSet
from apps.compendium.services import get_allowed_compendium_items_for_campaign


class CampaignViewSet(ModelViewSet):
    """Campaign CRUD endpoints"""

    serializer_class = CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.filter(members__user=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsCampaignDM()]
        return [IsAuthenticated()]  # List/Retrieve/Create

    def perform_create(self, serializer):
        campaign = serializer.save(created_by=self.request.user)
        # When creating Campaign set user as DM of this Campaign
        CampaignMembership.objects.create(
            user=self.request.user,
            campaign=campaign,
            role="DM"
        )


class CampaignInviteView(APIView):
    '''Create invite link for a Campaign.'''

    permission_classes = [IsAuthenticated, IsCampaignDM]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        self.check_object_permissions(request, campaign)
        invite = CampaignInvite.objects.create(
            campaign=campaign,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        invite_link = request.build_absolute_uri(
            reverse('campaign-invite-accept', args=[str(invite.token)])
        )
        return Response({
            "invite_link": invite_link,
            "expires_at": invite.expires_at
        }, status=status.HTTP_201_CREATED)


class CampaignAcceptInviteView(APIView):
    '''Accept invite to Campaign.'''

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invite = get_object_or_404(CampaignInvite, token=token)
        if not invite.is_valid():
            raise ValidationError({"detail": "Invite expired"})
        _, created = CampaignMembership.objects.get_or_create(
            user=request.user,
            campaign=invite.campaign,
            defaults={"role": CampaignMembership.Role.PLAYER}
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({
            "message": f"Joined campaign {invite.campaign.name} as Player.",
            "joined": created
        }, status=status_code)


class CampaignSourcesView(APIView):
    """
    Endpoint for getting and updating list of Sources in Campaign
    GET: List all allowed Sources for this Campaign (every Campaign member)
    PUT: Overwrite allowed Sources for this Campaign (only DM)
    """

    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAuthenticated(), IsCampaignDM()]
        return [IsAuthenticated(), IsCampaignMember()]  # GET

    def get_campaign(self, campaign_id):
        return get_object_or_404(
            Campaign.objects.filter(members__user=self.request.user),
            id=campaign_id
        )

    def get(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)
        self.check_object_permissions(request, campaign)
        sources = campaign.sources.all()
        return Response(SourceSerializer(sources, many=True).data)

    def put(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)
        self.check_object_permissions(request, campaign)
        serializer = CampaignSourceUpdateSerializer(
            instance=campaign,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SourceSerializer(campaign.sources.all(), many=True).data)


class CampaignItemRuleListCreateView(APIView):
    """
    Endpoint for listing and adding new Item Rules for Campaign.
    GET: List all Item Rules for this Campaign (every Campaign member)
    PUT: Adds a new Item Rule for this Campaign (only DM)
    """

    def get_campaign(self, campaign_id):
        return get_object_or_404(Campaign, id=campaign_id)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCampaignDM()]
        return [IsAuthenticated(), IsCampaignMember()]  # GET

    def get(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)
        self.check_object_permissions(request, campaign)
        rules = campaign.item_rules.all()
        return Response(
            CampaignItemRuleSerializer(rules, many=True).data
        )

    def post(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)
        self.check_object_permissions(request, campaign)
        serializer = CampaignItemRuleCreateSerializer(
            data=request.data,
            context={"campaign": campaign}
        )
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(
            CampaignItemRuleSerializer(rule).data,
            status=201
        )


class CampaignItemRuleDeleteView(generics.DestroyAPIView):

    serializer_class = CampaignItemRuleSerializer
    permission_classes = [IsAuthenticated, IsCampaignDM]

    lookup_field = "id"
    lookup_url_kwarg = "rule_id"

    def get_queryset(self):
        campaign = get_object_or_404(Campaign, id=self.kwargs["campaign_id"])
        return CampaignItemRule.objects.filter(campaign=campaign)


class CampaignSpellListView(generics.ListAPIView):

    serializer_class = SpellListSerializer
    permission_classes = [IsAuthenticated, IsCampaignMember]
    pagination_class = SpellViewSet.pagination_class
    filter_backends = SpellViewSet.filter_backends
    search_fields = SpellViewSet.search_fields
    ordering_fields = SpellViewSet.ordering_fields
    ordering = SpellViewSet.ordering

    def get_campaign(self):
        return get_object_or_404(Campaign, id=self.kwargs["campaign_id"])

    def get_queryset(self):
        campaign = self.get_campaign()
        self.check_object_permissions(self.request, campaign)
        return get_allowed_compendium_items_for_campaign(campaign, Spell)
