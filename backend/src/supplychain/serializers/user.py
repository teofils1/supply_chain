from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import serializers

import supplychain.models as m

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    active_role = serializers.CharField(source="profile.active_role")
    roles = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="profile.created_at", read_only=True)
    is_deleted = serializers.BooleanField(source="profile.is_deleted", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "active_role",
            "roles",
            "created_at",
            "is_deleted",
        ]

    def get_roles(self, obj):
        if hasattr(obj, "profile"):
            return obj.profile.roles
        # Only return active (non-soft-deleted) role assignments
        return list(obj.role_assignments.filter(deleted_at__isnull=True).values_list("role", flat=True))


class UserDetailSerializer(serializers.ModelSerializer):
    active_role = serializers.CharField(source="profile.active_role")
    roles = serializers.SerializerMethodField()
    roles_input = serializers.ListField(
        child=serializers.ChoiceField(choices=m.UserProfile.ROLE_CHOICES),
        write_only=True,
        required=False,
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    created_at = serializers.DateTimeField(source="profile.created_at", read_only=True)
    is_deleted = serializers.BooleanField(source="profile.is_deleted", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "active_role",
            "roles",
            "roles_input",
            "created_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "username"]

    def get_roles(self, obj):
        """Get the roles assigned to this user"""
        if hasattr(obj, "profile"):
            return obj.profile.roles
        # Only return active (non-soft-deleted) role assignments
        return list(obj.role_assignments.filter(deleted_at__isnull=True).values_list("role", flat=True))

    def validate(self, attrs):
        roles = attrs.get("roles_input")  # Changed from "roles" to "roles_input"
        # The active_role field has source="profile.active_role", so we need to check the profile data
        profile_data = attrs.get("profile", {})
        active_role = profile_data.get("active_role")

        if roles and active_role and active_role not in roles:
            raise serializers.ValidationError(
                "Active role must be included in roles list"
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        roles = validated_data.pop("roles_input", None)  # Changed from "roles" to "roles_input"
        password = validated_data.pop("password", None)

        # Update user fields first
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Get or create profile
        profile, _ = m.UserProfile.objects.get_or_create(user=instance)

        # Update active role if provided
        if "active_role" in profile_data:
            profile.active_role = profile_data["active_role"]
            profile.save()

        # Update role assignments if provided
        if roles is not None:
            # Get current active roles from database (excluding soft-deleted)
            current_role_assignments = instance.role_assignments.all()
            current_roles = {ra.role for ra in current_role_assignments}

            # Get all role assignments including soft-deleted ones
            all_role_assignments = instance.role_assignments.all_with_deleted()
            deleted_role_assignments = {ra.role: ra for ra in all_role_assignments.filter(deleted_at__isnull=False)}

            new_roles = set(roles)

            # Remove roles that are no longer needed (soft delete them)
            for role_assignment in current_role_assignments:
                if (role_assignment.role not in new_roles and
                    role_assignment.role != profile.active_role):
                    role_assignment.delete()  # This is a soft delete

            # Add new roles (restore if previously deleted, create if never existed)
            for role in new_roles:
                if role not in current_roles:
                    # Check if this role was previously assigned but soft-deleted
                    if role in deleted_role_assignments:
                        # Restore the soft-deleted role assignment
                        deleted_role_assignments[role].restore()
                    else:
                        # Create new role assignment
                        try:
                            m.RoleAssignment.objects.create(user=instance, role=role)
                        except Exception:
                            # Role assignment already exists, ignore
                            pass

        # Set password if provided
        if password:
            instance.set_password(password)
            instance.save()

        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    initial_role = serializers.ChoiceField(
        choices=m.UserProfile.ROLE_CHOICES, write_only=True
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    active_role = serializers.CharField(read_only=True, source="profile.active_role")
    roles = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="profile.created_at", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "initial_role",
            "active_role",
            "roles",
            "created_at",
        ]

    def get_roles(self, obj):
        return obj.profile.roles if hasattr(obj, "profile") else []

    def create(self, validated_data):
        initial_role = validated_data.pop("initial_role")
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        # Generate a secure random password if none supplied
        raw_password = password or get_random_string(length=14)
        user.set_password(raw_password)
        user.save()
        # Create profile & initial role
        profile = m.UserProfile.objects.create(user=user, active_role=initial_role)
        m.RoleAssignment.objects.create(user=user, role=initial_role)
        # Expose the raw password to the view for invitation email
        user._raw_password = raw_password
        profile.refresh_from_db()
        return user
