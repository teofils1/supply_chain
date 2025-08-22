from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import RoleAssignment, UserProfile
from ..serializers import UserCreateSerializer, UserDetailSerializer, UserListSerializer

User = get_user_model()


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )
        self.profile = UserProfile.objects.create(
            user=self.user, active_role="Operator"
        )
        RoleAssignment.objects.create(user=self.user, role="Operator")

    def test_user_list_serializer(self):
        """Test UserListSerializer output."""
        serializer = UserListSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["active_role"], "Operator")
        self.assertEqual(data["roles"], ["Operator"])
        self.assertFalse(data["is_deleted"])

    def test_user_list_serializer_with_deleted_profile(self):
        """Test UserListSerializer with soft-deleted profile."""
        self.profile.delete()

        serializer = UserListSerializer(self.user)
        data = serializer.data

        self.assertTrue(data["is_deleted"])

    def test_user_create_serializer(self):
        """Test UserCreateSerializer."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "initial_role": "Auditor",
        }

        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.profile.active_role, "Auditor")
        self.assertTrue(user.role_assignments.filter(role="Auditor").exists())
        self.assertTrue(hasattr(user, "_raw_password"))

    def test_user_detail_serializer_update(self):
        """Test UserDetailSerializer update functionality."""
        data = {
            "first_name": "Updated",
            "active_role": "Admin",
            "roles": ["Operator", "Admin"],
        }

        serializer = UserDetailSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.profile.active_role, "Admin")

        roles = set(updated_user.role_assignments.values_list("role", flat=True))
        self.assertEqual(roles, {"Operator", "Admin"})

    def test_user_detail_serializer_validation(self):
        """Test UserDetailSerializer validation."""
        data = {
            "active_role": "Admin",
            "roles": ["Operator"],  # Active role not in roles list
        }

        serializer = UserDetailSerializer(self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Active role must be included in roles list", str(serializer.errors)
        )

    def test_user_create_serializer_generates_password(self):
        """Test that UserCreateSerializer generates password when none provided."""
        data = {
            "username": "passuser",
            "email": "pass@example.com",
            "initial_role": "Operator",
        }

        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        raw_password = getattr(user, "_raw_password", None)

        self.assertIsNotNone(raw_password)
        self.assertEqual(len(raw_password), 14)  # Default length from get_random_string
        self.assertTrue(user.check_password(raw_password))
