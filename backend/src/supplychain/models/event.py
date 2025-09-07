from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .base import BaseModel
import hashlib
import json

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

    # Blockchain integrity fields
    blockchain_tx_hash = models.CharField(
        max_length=66,  # For Ethereum tx hash (0x + 64 hex chars)
        blank=True,
        null=True,
        help_text="Blockchain transaction hash for anchored event"
    )
    
    blockchain_block_number = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        help_text="Block number where the event was anchored"
    )
    
    integrity_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("anchored", "Anchored"),
            ("failed", "Failed"),
        ],
        default="pending",
        help_text="Status of blockchain anchoring",
        db_index=True,
    )
    
    event_hash = models.CharField(
        max_length=64,  # SHA-256 hash (64 hex chars)
        blank=True,
        null=True,
        help_text="SHA-256 hash of canonical event data",
        db_index=True,
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

    def compute_event_hash(self):
        """
        Compute SHA-256 hash of canonical JSON representation of event data.
        This hash is used for blockchain anchoring and integrity verification.
        """
        # Create canonical representation of event data
        canonical_data = {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "location": self.location,
            "metadata": self.metadata,
            "user_id": self.user_id if self.user else None,
        }
        
        # Sort keys to ensure consistent ordering
        canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))
        return hash_obj.hexdigest()

    def update_event_hash(self):
        """Update the event_hash field with computed hash."""
        self.event_hash = self.compute_event_hash()
        self.save(update_fields=['event_hash'])

    def verify_integrity(self):
        """
        Verify event integrity by comparing stored hash with computed hash.
        Returns True if integrity is verified, False otherwise.
        """
        if not self.event_hash:
            return False
        return self.event_hash == self.compute_event_hash()

    @property
    def is_blockchain_anchored(self):
        """Check if this event is anchored on blockchain."""
        return self.integrity_status == "anchored" and self.blockchain_tx_hash

    @property
    def blockchain_explorer_url(self):
        """Get blockchain explorer URL for this event's transaction."""
        if not self.blockchain_tx_hash:
            return None
        # Default to Ethereum mainnet explorer (can be configured)
        return f"https://etherscan.io/tx/{self.blockchain_tx_hash}"

    def mark_blockchain_anchored(self, tx_hash, block_number):
        """Mark event as successfully anchored on blockchain."""
        self.blockchain_tx_hash = tx_hash
        self.blockchain_block_number = block_number
        self.integrity_status = "anchored"
        self.save(update_fields=['blockchain_tx_hash', 'blockchain_block_number', 'integrity_status'])

    def mark_blockchain_failed(self):
        """Mark event blockchain anchoring as failed."""
        self.integrity_status = "failed"
        self.save(update_fields=['integrity_status'])
