from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from model_utils import FieldTracker

from ..validators import (
    validate_lot_number_format,
    validate_positive_quantity,
)
from .base import BaseModel
from .product import Product


class Batch(BaseModel):
    """Batch model representing production batches of products in the supply chain."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("recalled", "Recalled"),
        ("quarantined", "Quarantined"),
        ("released", "Released"),
        ("destroyed", "Destroyed"),
    ]

    # Core batch identification
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="batches",
        help_text="Product this batch belongs to",
    )
    lot_number = models.CharField(
        max_length=100,
        validators=[validate_lot_number_format],
        help_text="Unique lot number for this batch",
    )

    # Production information
    manufacturing_date = models.DateField(
        help_text="Date when the batch was manufactured"
    )
    expiry_date = models.DateField(help_text="Expiry date of the batch")
    quantity_produced = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total quantity produced in this batch",
    )
    available_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Available quantity remaining in this batch",
        default=0,
    )

    # Location and facility information
    manufacturing_location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Location where the batch was manufactured",
    )
    manufacturing_facility = models.CharField(
        max_length=255,
        blank=True,
        help_text="Facility or plant where the batch was manufactured",
    )

    # Status and quality control
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Current status of the batch",
    )
    quality_control_notes = models.TextField(
        blank=True, help_text="Quality control notes and observations"
    )
    quality_control_passed = models.BooleanField(
        default=True, help_text="Whether the batch passed quality control"
    )

    # Additional batch information
    batch_size = models.CharField(
        max_length=100,
        blank=True,
        help_text="Size or volume of the batch (e.g., '1000 units', '500L')",
    )
    supplier_batch_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's batch number if different from lot number",
    )

    # Regulatory and compliance
    regulatory_approval_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Regulatory approval number for this batch",
    )
    certificate_of_analysis = models.CharField(
        max_length=255, blank=True, help_text="Certificate of Analysis reference"
    )

    # Field tracker for automated event generation
    _field_tracker = FieldTracker()

    class Meta:
        ordering = ["-manufacturing_date", "lot_number"]
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        unique_together = [["product", "lot_number"]]
        indexes = [
            models.Index(fields=["lot_number"]),
            models.Index(fields=["product", "lot_number"]),
            models.Index(fields=["manufacturing_date"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["manufacturing_location"]),
        ]

    def __str__(self):
        return f"{self.product.name} - Lot {self.lot_number}"

    @property
    def is_expired(self) -> bool:
        """Check if the batch has expired."""
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until expiry (negative if already expired)."""
        delta = self.expiry_date - timezone.now().date()
        return delta.days

    @property
    def age_in_days(self) -> int:
        """Calculate age of the batch in days."""
        delta = timezone.now().date() - self.manufacturing_date
        return delta.days

    @property
    def shelf_life_remaining_percent(self) -> float:
        """Calculate remaining shelf life as a percentage."""
        total_shelf_life = (self.expiry_date - self.manufacturing_date).days
        if total_shelf_life <= 0:
            return 0.0

        days_remaining = self.days_until_expiry
        if days_remaining <= 0:
            return 0.0

        return (days_remaining / total_shelf_life) * 100

    @property
    def quantity_used(self) -> int:
        """Calculate quantity used (quantity_produced - available_quantity)."""
        return self.quantity_produced - self.available_quantity

    def has_sufficient_quantity(self, required_quantity: int) -> bool:
        """Check if batch has sufficient available quantity."""
        return self.available_quantity >= required_quantity

    def consume_quantity(self, quantity: int) -> bool:
        """
        Consume quantity from available stock.
        Returns True if successful, False if insufficient quantity.
        """
        if not self.has_sufficient_quantity(quantity):
            return False

        self.available_quantity -= quantity
        self.save(update_fields=["available_quantity"])
        return True

    def clean(self):
        """Validate model fields."""
        errors = {}

        # Validate that expiry date is after manufacturing date
        if (
            self.manufacturing_date
            and self.expiry_date
            and self.expiry_date <= self.manufacturing_date
        ):
            errors["expiry_date"] = "Expiry date must be after manufacturing date."

        # Validate that available quantity doesn't exceed quantity produced
        if (
            self.quantity_produced is not None
            and self.available_quantity is not None
            and self.available_quantity > self.quantity_produced
        ):
            errors[
                "available_quantity"
            ] = f"Available quantity ({self.available_quantity}) cannot exceed quantity produced ({self.quantity_produced})."

        # Validate positive quantities
        if self.quantity_produced is not None and self.quantity_produced <= 0:
            errors["quantity_produced"] = "Quantity produced must be greater than 0."

        if self.available_quantity is not None and self.available_quantity < 0:
            errors["available_quantity"] = "Available quantity cannot be negative."

        if errors:
            raise ValidationError(errors)

        # Auto-update status based on expiry
        if self.expiry_date and self.is_expired and self.status == "active":
            self.status = "expired"

    def save(self, *args, **kwargs):
        """Override save to run clean validation and initialize available_quantity."""
        # Initialize available_quantity to quantity_produced for new batches
        if self.pk is None and self.available_quantity == 0:
            self.available_quantity = self.quantity_produced

        self.clean()
        super().save(*args, **kwargs)
