from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from .base import BaseModel

User = get_user_model()


class UserProfile(BaseModel):
    ROLE_CHOICES = [
        ("Operator", "Operator"),
        ("Auditor", "Auditor"),
        ("Admin", "Admin"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    active_role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="Operator"
    )

    def __str__(self):  # pragma: no cover - simple repr
        return f"Profile({self.user.username}, active={self.active_role})"

    @property
    def roles(self) -> list[str]:
        # Only return active (non-soft-deleted) role assignments
        return list(self.user.role_assignments.filter(deleted_at__isnull=True).values_list("role", flat=True))

    def has_role(self, role: str) -> bool:
        # Only check active (non-soft-deleted) role assignments
        return self.user.role_assignments.filter(role=role, deleted_at__isnull=True).exists()


class RoleAssignment(BaseModel):
    ROLE_CHOICES = UserProfile.ROLE_CHOICES
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    granted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ("user", "role")
        verbose_name = "Role Assignment"
        verbose_name_plural = "Role Assignments"

    def __str__(self):  # pragma: no cover - simple repr
        return f"{self.user.username}:{self.role}"
