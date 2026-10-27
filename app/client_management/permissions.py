from rest_framework.permissions import BasePermission

from .models import Client


class IsClient(BasePermission):
    """Allow only requests authenticated as a valid scrape client."""

    def has_permission(self, request, view):
        return isinstance(request.user, Client)
