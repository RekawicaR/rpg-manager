from rest_framework.permissions import BasePermission
from .models import User


class IsModerator(BasePermission):
    '''Custom permission to check if the requesting user is a Moderator'''

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.GlobalRole.MODERATOR)
