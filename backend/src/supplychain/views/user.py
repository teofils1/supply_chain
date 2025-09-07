from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .. import models as m
from .. import permissions as p
from .. import serializers as s

User = get_user_model()


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().select_related("profile")
    permission_classes = [IsAuthenticated, p.UserManagementPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return s.UserCreateSerializer
        return s.UserListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter out users with soft-deleted profiles
        qs = qs.filter(profile__deleted_at__isnull=True)
        # Ensure every superuser has a profile & Admin role
        for user in qs:
            if user.is_superuser:
                profile, created = m.UserProfile.objects.get_or_create(
                    user=user, defaults={"active_role": "Admin"}
                )
                if created or not user.role_assignments.filter(role="Admin").exists():
                    m.RoleAssignment.objects.get_or_create(user=user, role="Admin")
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        user = serializer.save()
        # Raw password generated in serializer (or provided) is attached as _raw_password
        raw_password = getattr(user, "_raw_password", None)
        # Ensure active role part of roles set
        profile = getattr(user, "profile", None)
        if (
            profile
            and not user.role_assignments.filter(role=profile.active_role).exists()
        ):
            m.RoleAssignment.objects.create(user=user, role=profile.active_role)
        self._send_invitation_email(user, raw_password)

    def _send_invitation_email(self, user, password: str):
        """Send invitation email with login credentials."""
        if not password:
            print(f"Warning: No password provided for user {user.username}")
            return

        subject = "Welcome to Supply Chain Tracking System - Account Created"

        # Create a more professional email message
        user_name = user.get_full_name() or user.username
        message = f"""Hello {user_name},

        Your account has been successfully created for the Supply Chain Tracking System.

        Login Credentials:
        Username: {user.username}
        Password: {password}
        Email: {user.email}
        Role: {getattr(user.profile, "active_role", "N/A")}

        Please log in and change your password immediately for security purposes.

        If you have any questions, please contact your system administrator.

        Best regards,
        Supply Chain Tracking System Team
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=False,  # Raise exceptions for debugging
            )
            print(f"Invitation email sent successfully to {user.email}")
        except Exception as e:
            print(f"Failed to send invitation email to {user.email}: {str(e)}")
            # In production, you might want to log this or notify admins


class UserDetailUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all().select_related("profile")
    permission_classes = [IsAuthenticated, p.UserManagementPermission]
    serializer_class = s.UserDetailSerializer

    def get_queryset(self):
        # Include soft-deleted users for detail view (admins might need to see them)
        return super().get_queryset()

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all().select_related("profile")
    permission_classes = [IsAuthenticated, p.UserManagementPermission]

    def get_queryset(self):
        # Only allow deletion of users with profiles (don't allow deleting superusers without profiles)
        return super().get_queryset().filter(profile__isnull=False)

    def perform_destroy(self, instance):
        """Soft delete the user by soft-deleting their profile and role assignments."""
        # Prevent self-deletion
        if instance == self.request.user:
            return Response(
                {"error": "Cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Soft delete profile and role assignments
        if hasattr(instance, "profile"):
            instance.profile.delete()  # This is soft delete due to BaseModel

        # Soft delete role assignments
        instance.role_assignments.all().delete()  # This is soft delete due to BaseModel

        # Deactivate the user account instead of deleting the User object itself
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """Override to return proper response after soft delete."""
        instance = self.get_object()

        # Prevent self-deletion
        if instance == request.user:
            return Response(
                {"error": "Cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_destroy(instance)
        return Response(
            {"message": "User deleted successfully"}, status=status.HTTP_200_OK
        )
