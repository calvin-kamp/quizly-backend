"""Custom permissions for the quiz endpoints."""

from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allow access to a quiz only to the user who owns it."""

    def has_object_permission(self, request, view, obj):
        """Return ``True`` if the requesting user is the owner of ``obj``."""
        return obj.owner == request.user
