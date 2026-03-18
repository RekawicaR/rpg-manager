from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Campaign, CampaignMembership
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
