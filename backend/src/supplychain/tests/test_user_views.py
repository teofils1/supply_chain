from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import AccessToken

import supplychain.models as m

User = get_user_model()


class UserViewsTests(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_superuser=True,
        )
        self.admin_profile = m.UserProfile.objects.create(
            user=self.admin_user, active_role="Admin"
        )
        m.RoleAssignment.objects.create(user=self.admin_user, role="Admin")

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="regularpass123"
        )
        self.regular_profile = m.UserProfile.objects.create(
            user=self.regular_user, active_role="Operator"
        )
        m.RoleAssignment.objects.create(user=self.regular_user, role="Operator")

        # Set up API client with admin authentication
        self.client = APIClient()
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

    def test_list_users(self):
        """Test listing users."""
        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # admin and regular user

    def test_create_user(self):
        """Test creating a new user."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "initial_role": "Auditor",
        }

        response = self.client.post("/api/users/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)

        new_user = User.objects.get(username="newuser")
        self.assertEqual(new_user.profile.active_role, "Auditor")
        self.assertTrue(new_user.role_assignments.filter(role="Auditor").exists())

    def test_update_user(self):
        """Test updating a user."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "active_role": "Admin",
            "roles": ["Operator", "Admin"],
        }

        response = self.client.patch(f"/api/users/{self.regular_user.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, "Updated")
        self.assertEqual(self.regular_user.profile.active_role, "Admin")

    def test_delete_user(self):
        """Test soft deleting a user."""
        response = self.client.delete(f"/api/users/{self.regular_user.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User should still exist but be deactivated
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

        # Profile should be soft deleted
        self.regular_profile.refresh_from_db()
        self.assertTrue(self.regular_profile.is_deleted)

    def test_cannot_delete_self(self):
        """Test that admin cannot delete their own account."""
        response = self.client.delete(f"/api/users/{self.admin_user.id}/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot delete your own account", response.data["error"])

    def test_non_admin_cannot_access(self):
        """Test that non-admin users cannot access user management."""
        # Authenticate as regular user
        regular_token = str(AccessToken.for_user(self.regular_user))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {regular_token}")

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access user management."""
        self.client.credentials()  # Remove authentication

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_excludes_deleted_users(self):
        """Test that listing users excludes soft-deleted ones."""
        # Soft delete regular user
        self.regular_profile.delete()

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only admin user should be visible
