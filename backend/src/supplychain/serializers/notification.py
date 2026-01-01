"""
Serializers for the notification system.
"""

from rest_framework import serializers

from supplychain.models import NotificationLog, NotificationRule
from supplychain.serializers.event import EventDetailSerializer


class NotificationRuleSerializer(serializers.ModelSerializer):
    """Serializer for NotificationRule model."""

    class Meta:
        model = NotificationRule
        fields = [
            "id",
            "user",
            "name",
            "event_types",
            "severity_levels",
            "channels",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate notification rule data."""
        # Ensure user matches request user
        request = self.context.get("request")
        if request and request.user:
            data["user"] = request.user
        return data


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for NotificationLog model."""

    event = EventDetailSerializer(read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "event",
            "user",
            "user_email",
            "rule",
            "rule_name",
            "channel",
            "status",
            "sent_at",
            "acknowledged_at",
            "error_message",
            "escalated",
            "escalated_to",
            "escalated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "event",
            "user",
            "user_email",
            "rule",
            "rule_name",
            "channel",
            "status",
            "sent_at",
            "error_message",
            "escalated",
            "escalated_to",
            "escalated_at",
            "created_at",
        ]


class NotificationLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification log (acknowledgment)."""

    class Meta:
        model = NotificationLog
        fields = ["acknowledged_at"]
