from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .base import BaseModel

User = get_user_model()


class Event(BaseModel):
    """
    Model to track supply chain events for audit trail and monitoring.

    This model provides a comprehensive event tracking system that can be associated
    with any entity in the supply chain (Product, Batch, Pack, Shipment) and tracks
    various types of events with metadata, location, and severity information.
    """

    # Event Types
    EVENT_TYPE_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
        ("status_changed", "Status Changed"),
        ("location_changed", "Location Changed"),
        ("quality_check", "Quality Check"),
        ("temperature_alert", "Temperature Alert"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("returned", "Returned"),
        ("damaged", "Damaged"),
        ("expired", "Expired"),
        ("recalled", "Recalled"),
        ("inventory_count", "Inventory Count"),
        ("maintenance", "Maintenance"),
        ("calibration", "Calibration"),
        ("user_action", "User Action"),
        ("system_action", "System Action"),
        ("alert", "Alert"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("other", "Other"),
    ]

    # Entity Types (for the entities this event can be associated with)
    ENTITY_TYPE_CHOICES = [
        ("product", "Product"),
        ("batch", "Batch"),
        ("pack", "Pack"),
        ("shipment", "Shipment"),
        ("user", "User"),
        ("device", "Device"),
        ("location", "Location"),
        ("system", "System"),
    ]

    # Severity Levels
    SEVERITY_CHOICES = [
        ("info", "Information"),
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    # Core event information
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event that occurred",
    )

    # Generic foreign key to associate with any model
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        help_text="Type of entity this event is associated with",
    )
    entity_id = models.PositiveIntegerField(
        help_text="ID of the entity this event is associated with"
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Content type of the associated entity",
    )
    content_object = GenericForeignKey("content_type", "entity_id")

    # Event details
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="When the event occurred", db_index=True
    )

    description = models.TextField(help_text="Human-readable description of the event")

    # Event metadata (JSON field for flexible data storage)
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional event data in JSON format"
    )

    # Event context
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="info",
        help_text="Severity level of the event",
        db_index=True,
    )

    location = models.CharField(
        max_length=255, blank=True, help_text="Location where the event occurred"
    )

    # User who triggered the event (if applicable)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="User who triggered this event",
    )

    # Additional tracking fields
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="IP address from which the event was triggered"
    )

    user_agent = models.TextField(
        blank=True, help_text="User agent string from the request"
    )

    # System information
    system_info = models.JSONField(
        default=dict, blank=True, help_text="System information when the event occurred"
    )

    class Meta:
        db_table = "supplychain_event"
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["entity_type"]),
            models.Index(fields=["entity_id"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["user"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["event_type", "timestamp"]),
            models.Index(fields=["severity", "timestamp"]),
        ]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        entity_info = (
            f"{self.entity_type}#{self.entity_id}" if self.entity_id else "System"
        )
        return f"{self.get_event_type_display()} - {entity_info} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

    @property
    def entity_display_name(self):
        """Get a human-readable name for the associated entity."""
        if self.content_object:
            if hasattr(self.content_object, "name"):
                return self.content_object.name
            elif hasattr(self.content_object, "tracking_number"):
                return self.content_object.tracking_number
            elif hasattr(self.content_object, "serial_number"):
                return self.content_object.serial_number
            elif hasattr(self.content_object, "lot_number"):
                return self.content_object.lot_number
            elif hasattr(self.content_object, "username"):
                return self.content_object.username
        return f"{self.entity_type}#{self.entity_id}"

    @property
    def is_critical(self):
        """Check if this is a critical event."""
        return self.severity == "critical"

    @property
    def is_alert(self):
        """Check if this event should trigger an alert."""
        return self.severity in ["high", "critical"] or self.event_type in [
            "temperature_alert",
            "damaged",
            "recalled",
            "error",
        ]

    def get_related_entity_info(self):
        """Get information about the related entity."""
        if not self.content_object:
            return None

        entity_info = {
            "type": self.entity_type,
            "id": self.entity_id,
            "name": self.entity_display_name,
        }

        # Add specific information based on entity type
        if self.entity_type == "product" and hasattr(self.content_object, "gtin"):
            entity_info["gtin"] = self.content_object.gtin
        elif self.entity_type == "batch" and hasattr(self.content_object, "product"):
            entity_info["product_name"] = self.content_object.product.name
        elif self.entity_type == "pack" and hasattr(self.content_object, "batch"):
            entity_info["batch_lot_number"] = self.content_object.batch.lot_number
            entity_info["product_name"] = self.content_object.batch.product.name
        elif self.entity_type == "shipment" and hasattr(self.content_object, "carrier"):
            entity_info["carrier"] = self.content_object.carrier
            entity_info["status"] = self.content_object.status

        return entity_info

    @classmethod
    def create_event(
        cls,
        event_type,
        entity_type,
        entity_id,
        description,
        user=None,
        severity="info",
        location="",
        metadata=None,
        ip_address=None,
        user_agent="",
        system_info=None,
    ):
        """
        Convenience method to create an event.

        Args:
            event_type: Type of event (from EVENT_TYPE_CHOICES)
            entity_type: Type of entity (from ENTITY_TYPE_CHOICES)
            entity_id: ID of the entity
            description: Human-readable description
            user: User who triggered the event (optional)
            severity: Severity level (default: 'info')
            location: Location where event occurred (optional)
            metadata: Additional event data (optional)
            ip_address: IP address (optional)
            user_agent: User agent string (optional)
            system_info: System information (optional)

        Returns:
            Event: Created event instance
        """
        return cls.objects.create(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            user=user,
            severity=severity,
            location=location,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            system_info=system_info or {},
        )
