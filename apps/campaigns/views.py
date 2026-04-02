from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .permissions import IsCampaignDM, IsCampaignMember
from .models import Campaign, CampaignMembership, CampaignInvite, CampaignItemRule
from .serializers import CampaignSerializer, CampaignSourceUpdateSerializer, CampaignItemRuleCreateSerializer, CampaignItemRuleSerializer
from apps.compendium.serializers.source import SourceSerializer


class CampaignCreateView(generics.CreateAPIView):
    '''Create a Campaign and set a user creating this campaign as a DM.'''

    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        campaign = serializer.save(created_by=self.request.user)

        CampaignMembership.objects.create(
            user=self.request.user,
            campaign=campaign,
            role="DM"
        )


class CampaignListView(generics.ListAPIView):
    '''Return all campaigns in which the user that sends the request is a member.'''

    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Campaign.objects.filter(
            members__user=self.request.user
        )


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    → access for Campaign members
    PATCH  → only DM
    DELETE → only DM
    """

    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    lookup_field = "id"
    lookup_url_kwarg = "campaign_id"

    def get_queryset(self):
        return Campaign.objects.filter(
            members__user=self.request.user
        )

    def get_permissions(self):
        # Read-only operations (GET, HEAD, OPTIONS)
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        # Write operations (PATCH, DELETE)
        return [IsAuthenticated(), IsCampaignDM()]


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

    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invite = CampaignInvite.objects.get(token=token)

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
    GET: every Campaign member
    PUT: only DM
    """

    permission_classes = [IsAuthenticated]

    def get_campaign(self, campaign_id):
        return get_object_or_404(Campaign, id=campaign_id)

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

    def get_permissions(self):

        if self.request.method == "GET":
            return [IsAuthenticated(), IsCampaignMember()]

        return [IsAuthenticated(), IsCampaignDM()]


class CampaignItemRuleListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get_campaign(self, campaign_id):
        return get_object_or_404(Campaign, id=campaign_id)

    def get_permissions(self):

        if self.request.method == "GET":
            return [IsAuthenticated(), IsCampaignMember()]

        return [IsAuthenticated(), IsCampaignDM()]

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
