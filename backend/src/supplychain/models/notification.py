"""
Notification models for the supply chain notification system.

This module provides models for configurable notification rules,
notification logs, and escalation tracking.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from .base import BaseModel


class NotificationRule(BaseModel):
    """
    Configurable notification rules per user.

    Users can configure which event types and severity levels
    trigger notifications, and through which channels.
    """

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("websocket", "WebSocket (Real-time)"),
        ("sms", "SMS"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_rules",
    )
    name = models.CharField(max_length=100, help_text="Rule name for identification")

    # Event filtering
    event_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of event types to notify on (empty = all)",
    )
    severity_levels = models.JSONField(
        default=list,
        blank=True,
        help_text="List of severity levels to notify on (empty = all)",
    )

    # Notification channels
    channels = models.JSONField(
        default=list,
        help_text="List of channels: email, websocket, sms",
    )

    # Rule status
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notification Rule"
        verbose_name_plural = "Notification Rules"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def matches_event(self, event) -> bool:
        """Check if this rule matches the given event."""
        if not self.enabled:
            return False

        # Check event type (empty list = match all)
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check severity (empty list = match all)
        if self.severity_levels and event.severity not in self.severity_levels:
            return False

        return True


class NotificationLog(BaseModel):
    """
    Log of sent notifications for audit and tracking.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("acknowledged", "Acknowledged"),
    ]

    event = models.ForeignKey(
        "supplychain.Event",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    rule = models.ForeignKey(
        NotificationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    channel = models.CharField(max_length=20, choices=NotificationRule.CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Delivery details
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    # For escalation tracking
    escalated = models.BooleanField(default=False)
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalated_notifications",
    )
    escalated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["event", "channel"]),
        ]

    def __str__(self):
        return f"Notification to {self.user.username} via {self.channel} ({self.status})"
