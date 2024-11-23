from rest_framework.permissions import BasePermission
from .models import PlatformAccess


class HasPaidPlatformAccess(BasePermission):
    """
    Custom permission to only allow users who have successfully paid for the platform access.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has a successful payment
        return PlatformAccess.objects.filter(
            user=request.user, status="SUCCESS"
        ).exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
