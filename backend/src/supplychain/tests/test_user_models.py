from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from ..models import BaseModel, RoleAssignment, UserProfile

User = get_user_model()


class BaseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.profile = UserProfile.objects.create(
            user=self.user, active_role="Operator"
        )

    def test_soft_delete(self):
        """Test that soft delete sets deleted_at timestamp."""
        self.assertIsNone(self.profile.deleted_at)
        self.assertFalse(self.profile.is_deleted)

        self.profile.delete()

        self.assertIsNotNone(self.profile.deleted_at)
        self.assertTrue(self.profile.is_deleted)

    def test_restore(self):
        """Test that restore clears deleted_at timestamp."""
        self.profile.delete()
        self.assertTrue(self.profile.is_deleted)

        self.profile.restore()

        self.assertIsNone(self.profile.deleted_at)
        self.assertFalse(self.profile.is_deleted)

    def test_hard_delete(self):
        """Test that hard delete permanently removes the object."""
        profile_id = self.profile.id
        self.profile.hard_delete()

        with self.assertRaises(UserProfile.DoesNotExist):
            UserProfile.all_objects.get(id=profile_id)

    def test_manager_excludes_deleted(self):
        """Test that default manager excludes soft-deleted objects."""
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(UserProfile.all_objects.count(), 1)

        self.profile.delete()

        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(UserProfile.all_objects.count(), 1)

    def test_queryset_soft_delete(self):
        """Test soft delete via queryset."""
        UserProfile.objects.filter(id=self.profile.id).delete()

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_deleted)


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_profile(self):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(user=self.user, active_role="Admin")

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.active_role, "Admin")
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_roles_property(self):
        """Test that roles property returns assigned roles."""
        profile = UserProfile.objects.create(user=self.user, active_role="Operator")

        RoleAssignment.objects.create(user=self.user, role="Operator")
        RoleAssignment.objects.create(user=self.user, role="Auditor")

        roles = profile.roles
        self.assertIn("Operator", roles)
        self.assertIn("Auditor", roles)
        self.assertEqual(len(roles), 2)

    def test_has_role(self):
        """Test has_role method."""
        profile = UserProfile.objects.create(user=self.user, active_role="Operator")

        RoleAssignment.objects.create(user=self.user, role="Operator")

        self.assertTrue(profile.has_role("Operator"))
        self.assertFalse(profile.has_role("Admin"))


class RoleAssignmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_role_assignment(self):
        """Test creating a role assignment."""
        assignment = RoleAssignment.objects.create(user=self.user, role="Admin")

        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.role, "Admin")
        self.assertIsNotNone(assignment.granted_at)

    def test_unique_user_role(self):
        """Test that user-role combination is unique."""
        RoleAssignment.objects.create(user=self.user, role="Admin")

        with self.assertRaises(IntegrityError):
            RoleAssignment.objects.create(user=self.user, role="Admin")

    def test_soft_delete_role_assignment(self):
        """Test soft deleting role assignments."""
        assignment = RoleAssignment.objects.create(user=self.user, role="Admin")

        self.assertEqual(RoleAssignment.objects.count(), 1)

        assignment.delete()

        self.assertEqual(RoleAssignment.objects.count(), 0)
        self.assertEqual(RoleAssignment.all_objects.count(), 1)
