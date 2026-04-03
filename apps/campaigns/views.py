from rest_framework.viewsets import ModelViewSet
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .permissions import IsCampaignDM, IsCampaignMember
from .models import Campaign, CampaignMembership, CampaignInvite, CampaignItemRule
from .serializers import (
    CampaignSerializer,
    CampaignSourceUpdateSerializer,
    CampaignItemRuleCreateSerializer,
    CampaignItemRuleSerializer
)
from apps.compendium.serializers.source import SourceSerializer


class CampaignViewSet(ModelViewSet):
    """Campaign CRUD endpoints"""
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Campaign.objects.filter(members__user=self.request.user)

    def get_permissions(self):
        """
        List/Retrieve/Create: IsAuthenticated
        Update/Delete: IsAuthenticated + IsCampaignDM
        """
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsCampaignDM()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        campaign = serializer.save(created_by=self.request.user)
        CampaignMembership.objects.create(
            user=self.request.user,
            campaign=campaign,
            role="DM"
        )


class CampaignRulesListCreateView(generics.ListCreateAPIView):
    """List and create campaign item rules"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CampaignItemRuleCreateSerializer
        return CampaignItemRuleSerializer

    def get_campaign(self):
        return get_object_or_404(Campaign, id=self.kwargs["campaign_id"])

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return CampaignItemRule.objects.filter(campaign__members__user=self.request.user, campaign_id=campaign_id)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCampaignDM()]
        return [IsAuthenticated(), IsCampaignMember()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["campaign"] = self.get_campaign()
        return context

    def list(self, request, *args, **kwargs):
        campaign = self.get_campaign()
        self.check_object_permissions(request, campaign)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        campaign = self.get_campaign()
        self.check_object_permissions(request, campaign)

        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        rule = input_serializer.save()

        output_serializer = CampaignItemRuleSerializer(rule)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class CampaignRuleDestroyView(generics.DestroyAPIView):
    """Delete a campaign item rule"""
    serializer_class = CampaignItemRuleSerializer
    permission_classes = [IsAuthenticated, IsCampaignDM]
    lookup_field = "id"
    lookup_url_kwarg = "rule_id"

    def get_queryset(self):
        campaign_id = self.kwargs['campaign_id']
        return CampaignItemRule.objects.filter(campaign__members__user=self.request.user, campaign_id=campaign_id)


class CampaignSourcesView(APIView):
    """Get and replace campaign sources (non-standard operation)"""
    permission_classes = [IsAuthenticated]

    def get_campaign(self, campaign_id):
        return get_object_or_404(
            Campaign.objects.filter(members__user=self.request.user),
            id=campaign_id
        )

    def get(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)
        sources = campaign.sources.all()
        return Response(SourceSerializer(sources, many=True).data)

    def put(self, request, campaign_id):
        campaign = self.get_campaign(campaign_id)

        if not IsCampaignDM().has_object_permission(request, self, campaign):
            return Response(
                {"detail": "Only campaign DM can update sources"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CampaignSourceUpdateSerializer(
            instance=campaign,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(SourceSerializer(campaign.sources.all(), many=True).data)


class CampaignInviteView(APIView):
    """Create invite link for a Campaign"""
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
    """Accept invite to campaign (custom logic)"""
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
