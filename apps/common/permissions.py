"""
Permission classes for Event Planner project.
"""

from rest_framework import permissions


class IsBusinessOwner(permissions.BasePermission):
    """
    Permission check for business owners.
    """

    def has_permission(self, request, view):
        """
        Check if user is owner of current business.
        """
        if not request.user.is_authenticated:
            return False

        current_business = getattr(request.user, 'current_business', None)
        if not current_business:
            return False

        membership = request.user.business_memberships.filter(
            business=current_business,
            role='owner'
        ).first()

        return membership is not None


class IsBusinessAdmin(permissions.BasePermission):
    """
    Permission check for business admins (includes owners).
    """

    def has_permission(self, request, view):
        """
        Check if user is admin or owner of current business.
        """
        if not request.user.is_authenticated:
            return False

        current_business = getattr(request.user, 'current_business', None)
        if not current_business:
            return False

        membership = request.user.business_memberships.filter(
            business=current_business,
            role__in=['owner', 'admin']
        ).first()

        return membership is not None


class IsBusinessMember(permissions.BasePermission):
    """
    Permission check for any business member.
    """

    def has_permission(self, request, view):
        """
        Check if user is a member of current business.
        """
        if not request.user.is_authenticated:
            return False

        current_business = getattr(request.user, 'current_business', None)
        if not current_business:
            return False

        return request.user.business_memberships.filter(
            business=current_business
        ).exists()


class IsBusinessOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to members, write access to owners.
    """

    def has_permission(self, request, view):
        """
        Check permissions based on request method.
        """
        if not request.user.is_authenticated:
            return False

        current_business = getattr(request.user, 'current_business', None)
        if not current_business:
            return False

        if request.method in permissions.SAFE_METHODS:
            return request.user.business_memberships.filter(
                business=current_business
            ).exists()

        return request.user.business_memberships.filter(
            business=current_business,
            role='owner'
        ).exists()


class IsBusinessAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to members, write access to admins/owners.
    """

    def has_permission(self, request, view):
        """
        Check permissions based on request method.
        """
        if not request.user.is_authenticated:
            return False

        current_business = getattr(request.user, 'current_business', None)
        if not current_business:
            return False

        if request.method in permissions.SAFE_METHODS:
            return request.user.business_memberships.filter(
                business=current_business
            ).exists()

        return request.user.business_memberships.filter(
            business=current_business,
            role__in=['owner', 'admin']
        ).exists()
