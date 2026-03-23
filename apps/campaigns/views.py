from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .permissions import IsCampaignDM
from .models import Campaign, CampaignMembership, CampaignInvite
from .serializers import CampaignSerializer


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
    '''Return all campaings in which the user that sends the request is a member.'''

    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Campaign.objects.filter(
            members__user=self.request.user
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
