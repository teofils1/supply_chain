from __future__ import annotations

from django.contrib.auth import get_user_model
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

    def get_roles(self, obj: User):
        if hasattr(obj, "profile"):
            return obj.profile.roles
        return list(obj.role_assignments.values_list("role", flat=True))


class UserDetailSerializer(serializers.ModelSerializer):
    active_role = serializers.CharField(source="profile.active_role")
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=m.UserProfile.ROLE_CHOICES),
        write_only=True,
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
            "created_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "username"]

    def validate(self, attrs):
        roles = attrs.get("roles")
        active_role = attrs.get("profile", {}).get("active_role")
        if roles and active_role and active_role not in roles:
            raise serializers.ValidationError(
                "Active role must be included in roles list"
            )
        return attrs

    def update(self, instance: User, validated_data):
        profile_data = validated_data.pop("profile", {})
        roles = validated_data.pop("roles", None)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        profile, _ = m.UserProfile.objects.get_or_create(user=instance)
        if "active_role" in profile_data:
            profile.active_role = profile_data["active_role"]
            profile.save()

        if roles is not None:
            # Sync role assignments
            current = set(profile.roles)
            new = set(roles)
            # Add new roles
            for role in new - current:
                m.RoleAssignment.objects.get_or_create(user=instance, role=role)
            # Remove roles not present (except ensure active role retained)
            for role in current - new:
                if role == profile.active_role:
                    continue
                m.RoleAssignment.objects.filter(user=instance, role=role).delete()

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

    def get_roles(self, obj: User):
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
