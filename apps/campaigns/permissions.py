from rest_framework.permissions import BasePermission
from .models import CampaignMembership, Campaign


class IsCampaignDM(BasePermission):
    '''Custom permission to check if the requesting user is a DM
    for the specific Campaign obejct being accessed.'''

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Campaign):
            return False
        return CampaignMembership.objects.filter(
            user=request.user,
            campaign=obj,
            role=CampaignMembership.Role.DM
        ).exists()


class IsCampaignMember(BasePermission):
    '''Custom permission to check if the requesting user is a member
    for the specific Campaign obejct being accessed.'''

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Campaign):
            return False
        return CampaignMembership.objects.filter(
            user=request.user,
            campaign=obj
        ).exists()
