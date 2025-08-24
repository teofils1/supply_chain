from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .base import BaseModel
from .batch import Batch


class Pack(BaseModel):
    """Pack model representing individual packs/packages of batches in the supply chain."""

    PACK_TYPE_CHOICES = [
        ("bottle", "Bottle"),
        ("box", "Box"),
        ("blister", "Blister Pack"),
        ("vial", "Vial"),
        ("tube", "Tube"),
        ("sachet", "Sachet"),
        ("ampoule", "Ampoule"),
        ("syringe", "Syringe"),
        ("inhaler", "Inhaler"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("damaged", "Damaged"),
        ("recalled", "Recalled"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("returned", "Returned"),
        ("quarantined", "Quarantined"),
        ("destroyed", "Destroyed"),
    ]

    # Core pack identification
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="packs",
        help_text="Batch this pack belongs to",
    )
    serial_number = models.CharField(
        max_length=100, unique=True, help_text="Unique serial number for this pack"
    )

    # Pack characteristics
    pack_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Number of units in this pack"
    )
    pack_type = models.CharField(
        max_length=20, choices=PACK_TYPE_CHOICES, help_text="Type of packaging"
    )

    # Pack-specific dates (can override batch dates if needed)
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Pack-specific manufacturing date (if different from batch)",
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Pack-specific expiry date (if different from batch)",
    )

    # Location and status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Current status of the pack",
    )
    location = models.CharField(
        max_length=255, blank=True, help_text="Current location/warehouse of the pack"
    )
    warehouse_section = models.CharField(
        max_length=100, blank=True, help_text="Specific section within the warehouse"
    )

    # Quality control and compliance
    quality_control_notes = models.TextField(
        blank=True, help_text="Pack-specific quality control notes"
    )
    quality_control_passed = models.BooleanField(
        default=True, help_text="Whether the pack passed quality control"
    )

    # Regulatory and tracking
    regulatory_code = models.CharField(
        max_length=100, blank=True, help_text="Regulatory tracking code for this pack"
    )
    customer_reference = models.CharField(
        max_length=100, blank=True, help_text="Customer reference number"
    )

    # Shipping information
    shipped_date = models.DateTimeField(
        null=True, blank=True, help_text="Date and time when the pack was shipped"
    )
    delivered_date = models.DateTimeField(
        null=True, blank=True, help_text="Date and time when the pack was delivered"
    )
    tracking_number = models.CharField(
        max_length=100, blank=True, help_text="Shipping tracking number"
    )

    class Meta:
        ordering = ["-created_at", "serial_number"]
        verbose_name = "Pack"
        verbose_name_plural = "Packs"
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["batch", "serial_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["location"]),
            models.Index(fields=["pack_type"]),
            models.Index(fields=["shipped_date"]),
            models.Index(fields=["delivered_date"]),
        ]

    def __str__(self):
        return f"Pack {self.serial_number} - {self.batch.product.name} (Lot {self.batch.lot_number})"

    @property
    def effective_manufacturing_date(self):
        """Return pack-specific manufacturing date or batch manufacturing date."""
        return self.manufacturing_date or self.batch.manufacturing_date

    @property
    def effective_expiry_date(self):
        """Return pack-specific expiry date or batch expiry date."""
        return self.expiry_date or self.batch.expiry_date

    @property
    def is_expired(self) -> bool:
        """Check if the pack has expired based on effective expiry date."""
        effective_expiry = self.effective_expiry_date
        return effective_expiry < timezone.now().date() if effective_expiry else False

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until expiry (negative if already expired)."""
        effective_expiry = self.effective_expiry_date
        if not effective_expiry:
            return 0
        delta = effective_expiry - timezone.now().date()
        return delta.days

    @property
    def product(self):
        """Get the product through the batch relationship."""
        return self.batch.product

    @property
    def product_name(self) -> str:
        """Get the product name through the batch relationship."""
        return self.batch.product.name

    @property
    def product_gtin(self) -> str:
        """Get the product GTIN through the batch relationship."""
        return self.batch.product.gtin

    @property
    def lot_number(self) -> str:
        """Get the batch lot number."""
        return self.batch.lot_number

    @property
    def is_shipped(self) -> bool:
        """Check if the pack has been shipped."""
        return self.status in ["shipped", "delivered"] or self.shipped_date is not None

    @property
    def is_delivered(self) -> bool:
        """Check if the pack has been delivered."""
        return self.status == "delivered" or self.delivered_date is not None

    def clean(self):
        """Validate model fields."""
        from django.core.exceptions import ValidationError

        # Validate dates if provided
        if self.manufacturing_date and self.expiry_date:
            if self.expiry_date <= self.manufacturing_date:
                raise ValidationError(
                    {
                        "expiry_date": "Pack expiry date must be after manufacturing date."
                    }
                )

        # Validate shipping dates
        if self.shipped_date and self.delivered_date:
            if self.delivered_date < self.shipped_date:
                raise ValidationError(
                    {"delivered_date": "Delivery date must be after shipping date."}
                )

        # Auto-update status based on shipping/delivery dates
        if self.delivered_date and self.status not in ["delivered", "returned"]:
            self.status = "delivered"
        elif self.shipped_date and self.status not in [
            "shipped",
            "delivered",
            "returned",
        ]:
            self.status = "shipped"

    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)
