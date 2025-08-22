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
