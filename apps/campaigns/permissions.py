from rest_framework.permissions import BasePermission
from .models import CampaignMembership, Campaign


class IsCampaignDM(BasePermission):
    '''Custom permission to check if the requesting user is a DM
    for the specific Campaign object being accessed.'''

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "campaign"):
            campaign = obj.campaign
        elif isinstance(obj, Campaign):
            campaign = obj
        else:
            return False
        return CampaignMembership.objects.filter(
            user=request.user,
            campaign=campaign,
            role=CampaignMembership.Role.DM
        ).exists()


class IsCampaignMember(BasePermission):
    '''Custom permission to check if the requesting user is a member
    for the specific Campaign object being accessed.'''

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "campaign"):
            campaign = obj.campaign
        elif isinstance(obj, Campaign):
            campaign = obj
        else:
            return False
        return CampaignMembership.objects.filter(
            user=request.user,
            campaign=campaign
        ).exists()
