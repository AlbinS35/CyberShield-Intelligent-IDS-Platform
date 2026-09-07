"""
RBAC Permission Classes
Role-based access control permissions for CyberShield API views.
"""

from rest_framework.permissions import BasePermission
from .models import User


class TenantScopedPermission(BasePermission):
    """Base permission: user must be authenticated and have a tenant."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.tenant)


class IsAnalyst(TenantScopedPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in (
            User.Role.ANALYST, User.Role.SUPER_ADMIN
        )


class IsInvestigator(TenantScopedPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in (
            User.Role.INVESTIGATOR, User.Role.SUPER_ADMIN
        )


class IsSysAdmin(TenantScopedPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in (
            User.Role.SYS_ADMIN, User.Role.SUPER_ADMIN
        )


class IsOrgManager(TenantScopedPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in (
            User.Role.ORG_MANAGER, User.Role.SUPER_ADMIN
        )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role == User.Role.SUPER_ADMIN)


class IsAnalystOrAbove(TenantScopedPermission):
    """Any authenticated tenant user can access."""
    def has_permission(self, request, view):
        return super().has_permission(request, view)
