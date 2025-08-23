from __future__ import annotations

from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .base import BaseModel
from .pack import Pack


class Shipment(BaseModel):
    """Shipment model representing shipments containing multiple packs in the supply chain."""
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("picked_up", "Picked Up"),
        ("in_transit", "In Transit"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("returned", "Returned"),
        ("cancelled", "Cancelled"),
        ("lost", "Lost"),
        ("damaged", "Damaged"),
    ]
    
    CARRIER_CHOICES = [
        ("fedex", "FedEx"),
        ("ups", "UPS"),
        ("dhl", "DHL"),
        ("usps", "USPS"),
        ("amazon", "Amazon Logistics"),
        ("local", "Local Courier"),
        ("internal", "Internal Transport"),
        ("other", "Other"),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ("standard", "Standard"),
        ("express", "Express"),
        ("overnight", "Overnight"),
        ("same_day", "Same Day"),
        ("ground", "Ground"),
        ("air", "Air"),
        ("freight", "Freight"),
        ("cold_chain", "Cold Chain"),
    ]
    
    TEMPERATURE_REQUIREMENT_CHOICES = [
        ("ambient", "Ambient (15-25°C)"),
        ("cool", "Cool (2-8°C)"),
        ("frozen", "Frozen (-15 to -25°C)"),
        ("ultra_cold", "Ultra Cold (-70 to -80°C)"),
        ("controlled", "Controlled Temperature"),
    ]
    
    # Core shipment identification
    tracking_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique tracking number for this shipment"
    )
    
    # Relationships
    packs = models.ManyToManyField(
        Pack,
        through='ShipmentPack',
        related_name='shipments',
        help_text="Packs included in this shipment"
    )
    
    # Status and carrier information
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the shipment"
    )
    carrier = models.CharField(
        max_length=20,
        choices=CARRIER_CHOICES,
        help_text="Shipping carrier"
    )
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        default="standard",
        help_text="Type of shipping service"
    )
    
    # Origin information
    origin_name = models.CharField(
        max_length=255,
        help_text="Origin facility or company name"
    )
    origin_address_line1 = models.CharField(
        max_length=255,
        help_text="Origin address line 1"
    )
    origin_address_line2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Origin address line 2"
    )
    origin_city = models.CharField(
        max_length=100,
        help_text="Origin city"
    )
    origin_state = models.CharField(
        max_length=100,
        help_text="Origin state/province"
    )
    origin_postal_code = models.CharField(
        max_length=20,
        help_text="Origin postal/ZIP code"
    )
    origin_country = models.CharField(
        max_length=100,
        help_text="Origin country"
    )
    
    # Destination information
    destination_name = models.CharField(
        max_length=255,
        help_text="Destination facility or company name"
    )
    destination_address_line1 = models.CharField(
        max_length=255,
        help_text="Destination address line 1"
    )
    destination_address_line2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Destination address line 2"
    )
    destination_city = models.CharField(
        max_length=100,
        help_text="Destination city"
    )
    destination_state = models.CharField(
        max_length=100,
        help_text="Destination state/province"
    )
    destination_postal_code = models.CharField(
        max_length=20,
        help_text="Destination postal/ZIP code"
    )
    destination_country = models.CharField(
        max_length=100,
        help_text="Destination country"
    )
    
    # Dates
    shipped_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when the shipment was shipped"
    )
    estimated_delivery_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimated delivery date and time"
    )
    actual_delivery_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual delivery date and time"
    )
    
    # Requirements and handling
    temperature_requirement = models.CharField(
        max_length=20,
        choices=TEMPERATURE_REQUIREMENT_CHOICES,
        default="ambient",
        help_text="Temperature requirement for the shipment"
    )
    special_handling_required = models.BooleanField(
        default=False,
        help_text="Whether special handling is required"
    )
    special_instructions = models.TextField(
        blank=True,
        help_text="Special handling instructions"
    )
    
    # Cost and billing
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Shipping cost"
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency for shipping cost"
    )
    billing_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Billing reference number"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the shipment"
    )
    external_tracking_url = models.URLField(
        blank=True,
        help_text="External tracking URL from carrier"
    )
    
    class Meta:
        ordering = ["-created_at", "tracking_number"]
        verbose_name = "Shipment"
        verbose_name_plural = "Shipments"
        indexes = [
            models.Index(fields=["tracking_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["carrier"]),
            models.Index(fields=["shipped_date"]),
            models.Index(fields=["estimated_delivery_date"]),
            models.Index(fields=["actual_delivery_date"]),
            models.Index(fields=["origin_city", "origin_state"]),
            models.Index(fields=["destination_city", "destination_state"]),
        ]
    
    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.status}"
    
    @property
    def is_delivered(self) -> bool:
        """Check if the shipment has been delivered."""
        return self.status == 'delivered' or self.actual_delivery_date is not None
    
    @property
    def is_in_transit(self) -> bool:
        """Check if the shipment is currently in transit."""
        return self.status in ['picked_up', 'in_transit', 'out_for_delivery']
    
    @property
    def is_completed(self) -> bool:
        """Check if the shipment is completed (delivered or returned)."""
        return self.status in ['delivered', 'returned']
    
    @property
    def pack_count(self) -> int:
        """Get the number of packs in this shipment."""
        return self.packs.count()
    
    @property
    def total_pack_size(self) -> int:
        """Get the total pack size (sum of all pack sizes)."""
        return sum(pack.pack_size for pack in self.packs.all())
    
    @property
    def origin_address(self) -> str:
        """Get formatted origin address."""
        address_parts = [
            self.origin_address_line1,
            self.origin_address_line2,
            f"{self.origin_city}, {self.origin_state} {self.origin_postal_code}",
            self.origin_country
        ]
        return ", ".join(part for part in address_parts if part)
    
    @property
    def destination_address(self) -> str:
        """Get formatted destination address."""
        address_parts = [
            self.destination_address_line1,
            self.destination_address_line2,
            f"{self.destination_city}, {self.destination_state} {self.destination_postal_code}",
            self.destination_country
        ]
        return ", ".join(part for part in address_parts if part)
    
    def clean(self):
        """Validate model fields."""
        from django.core.exceptions import ValidationError
        
        # Validate dates
        if self.shipped_date and self.estimated_delivery_date:
            if self.estimated_delivery_date < self.shipped_date:
                raise ValidationError({
                    'estimated_delivery_date': 'Estimated delivery date must be after shipped date.'
                })
        
        if self.shipped_date and self.actual_delivery_date:
            if self.actual_delivery_date < self.shipped_date:
                raise ValidationError({
                    'actual_delivery_date': 'Actual delivery date must be after shipped date.'
                })
        
        # Auto-update status based on delivery date
        if self.actual_delivery_date and self.status not in ['delivered', 'returned']:
            self.status = 'delivered'
        elif self.shipped_date and self.status == 'pending':
            self.status = 'in_transit'
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation."""
        self.clean()
        super().save(*args, **kwargs)


class ShipmentPack(BaseModel):
    """Intermediate model for the many-to-many relationship between Shipment and Pack."""
    
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name="shipment_packs"
    )
    pack = models.ForeignKey(
        Pack,
        on_delete=models.CASCADE,
        related_name="pack_shipments"
    )
    
    # Additional fields for the relationship
    quantity_shipped = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of this pack being shipped"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes specific to this pack in the shipment"
    )
    
    class Meta:
        unique_together = ['shipment', 'pack']
        verbose_name = "Shipment Pack"
        verbose_name_plural = "Shipment Packs"
        indexes = [
            models.Index(fields=["shipment", "pack"]),
        ]
    
    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.pack.serial_number}"
    
    def save(self, *args, **kwargs):
        """Override save to update pack status when added to shipment."""
        super().save(*args, **kwargs)
        
        # Update pack status based on shipment status
        if self.shipment.status in ['picked_up', 'in_transit', 'out_for_delivery']:
            self.pack.status = 'shipped'
            self.pack.shipped_date = self.shipment.shipped_date
            self.pack.save()
        elif self.shipment.status == 'delivered':
            self.pack.status = 'delivered'
            self.pack.delivered_date = self.shipment.actual_delivery_date
            self.pack.save()
