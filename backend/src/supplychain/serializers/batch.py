from __future__ import annotations

from rest_framework import serializers

from .. import models as m


class BatchListSerializer(serializers.ModelSerializer):
    """Serializer for batch list view with essential fields."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_gtin = serializers.CharField(source="product.gtin", read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    shelf_life_remaining_percent = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = m.Batch
        fields = [
            "id",
            "product",
            "product_name",
            "product_gtin",
            "lot_number",
            "manufacturing_date",
            "expiry_date",
            "quantity_produced",
            "manufacturing_location",
            "status",
            "quality_control_passed",
            "is_expired",
            "days_until_expiry",
            "shelf_life_remaining_percent",
            "created_at",
            "updated_at",
            "is_deleted",
        ]


class BatchDetailSerializer(serializers.ModelSerializer):
    """Serializer for batch detail view with all fields."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_gtin = serializers.CharField(source="product.gtin", read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    age_in_days = serializers.ReadOnlyField()
    shelf_life_remaining_percent = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = m.Batch
        fields = [
            "id",
            "product",
            "product_name",
            "product_gtin",
            "lot_number",
            "manufacturing_date",
            "expiry_date",
            "quantity_produced",
            "manufacturing_location",
            "manufacturing_facility",
            "status",
            "quality_control_notes",
            "quality_control_passed",
            "batch_size",
            "supplier_batch_number",
            "regulatory_approval_number",
            "certificate_of_analysis",
            "is_expired",
            "days_until_expiry",
            "age_in_days",
            "shelf_life_remaining_percent",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def validate_lot_number(self, value):
        """Validate lot number uniqueness within the product."""
        product = self.initial_data.get("product") or (
            self.instance.product.id if self.instance else None
        )

        if not product:
            raise serializers.ValidationError(
                "Product is required to validate lot number."
            )

        # Check uniqueness within the product (excluding current instance if updating)
        queryset = m.Batch.objects.filter(product_id=product, lot_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A batch with this lot number already exists for this product."
            )

        return value

    def validate(self, attrs):
        """Validate batch data."""
        manufacturing_date = attrs.get("manufacturing_date")
        expiry_date = attrs.get("expiry_date")

        # Validate date range
        if manufacturing_date and expiry_date and expiry_date <= manufacturing_date:
            raise serializers.ValidationError(
                {"expiry_date": "Expiry date must be after manufacturing date."}
            )

        # Validate quantity
        quantity_produced = attrs.get("quantity_produced")
        if quantity_produced is not None and quantity_produced <= 0:
            raise serializers.ValidationError(
                {"quantity_produced": "Quantity produced must be greater than zero."}
            )

        return attrs


class BatchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new batches."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_gtin = serializers.CharField(source="product.gtin", read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    shelf_life_remaining_percent = serializers.ReadOnlyField()

    class Meta:
        model = m.Batch
        fields = [
            "id",
            "product",
            "product_name",
            "product_gtin",
            "lot_number",
            "manufacturing_date",
            "expiry_date",
            "quantity_produced",
            "manufacturing_location",
            "manufacturing_facility",
            "status",
            "quality_control_notes",
            "quality_control_passed",
            "batch_size",
            "supplier_batch_number",
            "regulatory_approval_number",
            "certificate_of_analysis",
            "is_expired",
            "days_until_expiry",
            "shelf_life_remaining_percent",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "is_expired",
            "days_until_expiry",
            "shelf_life_remaining_percent",
        ]

    def validate_lot_number(self, value):
        """Validate lot number uniqueness within the product."""
        product = self.initial_data.get("product")

        if not product:
            raise serializers.ValidationError(
                "Product is required to validate lot number."
            )

        if m.Batch.objects.filter(product_id=product, lot_number=value).exists():
            raise serializers.ValidationError(
                "A batch with this lot number already exists for this product."
            )

        return value

    def validate(self, attrs):
        """Validate batch data."""
        manufacturing_date = attrs.get("manufacturing_date")
        expiry_date = attrs.get("expiry_date")

        # Validate date range
        if manufacturing_date and expiry_date and expiry_date <= manufacturing_date:
            raise serializers.ValidationError(
                {"expiry_date": "Expiry date must be after manufacturing date."}
            )

        # Validate quantity
        quantity_produced = attrs.get("quantity_produced")
        if quantity_produced is not None and quantity_produced <= 0:
            raise serializers.ValidationError(
                {"quantity_produced": "Quantity produced must be greater than zero."}
            )

        # Validate product exists and is active
        product = attrs.get("product")
        if product and product.status != "active":
            raise serializers.ValidationError(
                {"product": "Cannot create batch for inactive or discontinued product."}
            )

        return attrs
