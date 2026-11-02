from rest_framework.permissions import BasePermission
from .models import RoomParticipant


class IsInterviewer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(user=request.user, role=RoomParticipant.Roles.INTERVIEWER).exists()