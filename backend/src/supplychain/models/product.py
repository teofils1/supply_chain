from __future__ import annotations

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from model_utils import FieldTracker

from .base import BaseModel


class Product(BaseModel):
    """Product model representing pharmaceutical products in the supply chain."""

    FORM_CHOICES = [
        ("tablet", "Tablet"),
        ("capsule", "Capsule"),
        ("liquid", "Liquid"),
        ("injection", "Injection"),
        ("cream", "Cream"),
        ("ointment", "Ointment"),
        ("powder", "Powder"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("discontinued", "Discontinued"),
    ]

    # Core product identification
    gtin = models.CharField(
        max_length=14, unique=True, help_text="Global Trade Item Number (GTIN-14)"
    )
    name = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(blank=True, help_text="Product description")

    # Product characteristics
    form = models.CharField(
        max_length=20, choices=FORM_CHOICES, help_text="Physical form of the product"
    )
    strength = models.CharField(
        max_length=100, blank=True, help_text="Product strength (e.g., '500mg', '10ml')"
    )

    # Storage requirements
    storage_temp_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-50), MaxValueValidator(100)],
        help_text="Minimum storage temperature in Celsius",
    )
    storage_temp_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-50), MaxValueValidator(100)],
        help_text="Maximum storage temperature in Celsius",
    )
    storage_humidity_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum storage humidity percentage",
    )
    storage_humidity_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum storage humidity percentage",
    )

    # Product metadata
    manufacturer = models.CharField(
        max_length=255, blank=True, help_text="Product manufacturer"
    )
    ndc = models.CharField(
        max_length=11, blank=True, help_text="National Drug Code (NDC)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Product status",
    )

    # Regulatory information
    approval_number = models.CharField(
        max_length=100, blank=True, help_text="Regulatory approval number"
    )

    # Field tracker for automated event generation
    _field_tracker = FieldTracker()

    class Meta:
        ordering = ["name", "gtin"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["gtin"]),
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["manufacturer"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.gtin})"

    @property
    def storage_range_display(self) -> str:
        """Return a human-readable storage range string."""
        temp_range = ""
        humidity_range = ""

        if self.storage_temp_min is not None and self.storage_temp_max is not None:
            temp_range = f"{self.storage_temp_min}°C - {self.storage_temp_max}°C"
        elif self.storage_temp_min is not None:
            temp_range = f"≥{self.storage_temp_min}°C"
        elif self.storage_temp_max is not None:
            temp_range = f"≤{self.storage_temp_max}°C"

        if (
            self.storage_humidity_min is not None
            and self.storage_humidity_max is not None
        ):
            humidity_range = (
                f"{self.storage_humidity_min}% - {self.storage_humidity_max}% RH"
            )
        elif self.storage_humidity_min is not None:
            humidity_range = f"≥{self.storage_humidity_min}% RH"
        elif self.storage_humidity_max is not None:
            humidity_range = f"≤{self.storage_humidity_max}% RH"

        ranges = [r for r in [temp_range, humidity_range] if r]
        return ", ".join(ranges) if ranges else "No specific requirements"

    def clean(self):
        """Validate model fields."""
        from django.core.exceptions import ValidationError

        # Validate temperature range
        if (
            self.storage_temp_min is not None
            and self.storage_temp_max is not None
            and self.storage_temp_min > self.storage_temp_max
        ):
            raise ValidationError(
                {
                    "storage_temp_max": "Maximum temperature must be greater than minimum temperature."
                }
            )

        # Validate humidity range
        if (
            self.storage_humidity_min is not None
            and self.storage_humidity_max is not None
            and self.storage_humidity_min > self.storage_humidity_max
        ):
            raise ValidationError(
                {
                    "storage_humidity_max": "Maximum humidity must be greater than minimum humidity."
                }
            )
