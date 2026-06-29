"""
Serializers for the notification system.
"""

from rest_framework import serializers

from supplychain.models import Event, NotificationLog, NotificationRule
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
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate(self, data):
        """Validate notification rule data."""
        event_types = data.get("event_types", [])
        severity_levels = data.get("severity_levels", [])
        channels = data.get("channels", [])

        valid_event_types = {value for value, _label in Event.EVENT_TYPE_CHOICES}
        invalid_event_types = sorted(set(event_types) - valid_event_types)
        if invalid_event_types:
            raise serializers.ValidationError(
                {
                    "event_types": f"Invalid event types: {', '.join(invalid_event_types)}"
                }
            )

        valid_severity_levels = {value for value, _label in Event.SEVERITY_CHOICES}
        invalid_severity_levels = sorted(set(severity_levels) - valid_severity_levels)
        if invalid_severity_levels:
            raise serializers.ValidationError(
                {
                    "severity_levels": f"Invalid severity levels: {', '.join(invalid_severity_levels)}"
                }
            )

        valid_channels = {value for value, _label in NotificationRule.CHANNEL_CHOICES}
        invalid_channels = sorted(set(channels) - valid_channels)
        if invalid_channels:
            raise serializers.ValidationError(
                {"channels": f"Invalid channels: {', '.join(invalid_channels)}"}
            )

        # Ensure user matches request user
        request = self.context.get("request")
        if request and request.user:
            data["user"] = request.user
        return data

    def create(self, validated_data):
        """Create a rule for the authenticated user."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


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
