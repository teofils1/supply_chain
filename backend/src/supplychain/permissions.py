from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow only users with Admin role or superuser status."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        if profile and profile.active_role == "Admin":
            return True
        # fallback: any role assignment admin
        return user.role_assignments.filter(role="Admin").exists()


class IsOperatorOrAdmin(BasePermission):
    """Allow users with Operator or Admin role or superuser status."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        if profile and profile.active_role in ["Admin", "Operator"]:
            return True
        # fallback: check role assignments
        return user.role_assignments.filter(role__in=["Admin", "Operator"]).exists()


class IsAuditorOrHigher(BasePermission):
    """Allow users with Auditor, Operator, or Admin role or superuser status."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        if profile and profile.active_role in ["Admin", "Operator", "Auditor"]:
            return True
        # fallback: check role assignments
        return user.role_assignments.filter(
            role__in=["Admin", "Operator", "Auditor"]
        ).exists()


class RoleBasedCRUDPermission(BasePermission):
    """
    Role-based CRUD permissions:
    - Admin: Full CRUD access
    - Operator: Full CRUD access (except user management)
    - Auditor: Read-only access (GET only)
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        profile = getattr(user, "profile", None)
        if not profile:
            return False

        active_role = profile.active_role

        # Admin has full access
        if active_role == "Admin":
            return True

        # Operator has full CRUD access (but user management is handled separately)
        if active_role == "Operator":
            return True

        # Auditor has read-only access
        if active_role == "Auditor":
            return request.method in ["GET", "HEAD", "OPTIONS"]

        return False


class UserManagementPermission(BasePermission):
    """Only Admin role can access user management endpoints."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        if profile and profile.active_role == "Admin":
            return True
        # fallback: any role assignment admin
        return user.role_assignments.filter(role="Admin").exists()
