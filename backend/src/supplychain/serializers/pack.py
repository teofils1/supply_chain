from __future__ import annotations

from rest_framework import serializers

from .. import models as m


class PackListSerializer(serializers.ModelSerializer):
    """Serializer for pack list view with essential fields."""
    
    # Related fields from batch and product
    batch_lot_number = serializers.CharField(source="batch.lot_number", read_only=True)
    product_name = serializers.CharField(source="batch.product.name", read_only=True)
    product_gtin = serializers.CharField(source="batch.product.gtin", read_only=True)
    
    # Calculated fields
    effective_manufacturing_date = serializers.ReadOnlyField()
    effective_expiry_date = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    is_shipped = serializers.ReadOnlyField()
    is_delivered = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = m.Pack
        fields = [
            "id",
            "batch",
            "batch_lot_number",
            "product_name",
            "product_gtin",
            "serial_number",
            "pack_size",
            "pack_type",
            "status",
            "location",
            "effective_manufacturing_date",
            "effective_expiry_date",
            "is_expired",
            "days_until_expiry",
            "quality_control_passed",
            "is_shipped",
            "is_delivered",
            "shipped_date",
            "delivered_date",
            "created_at",
            "updated_at",
            "is_deleted",
        ]


class PackDetailSerializer(serializers.ModelSerializer):
    """Serializer for pack detail view with all fields."""
    
    # Related fields from batch and product
    batch_lot_number = serializers.CharField(source="batch.lot_number", read_only=True)
    product_name = serializers.CharField(source="batch.product.name", read_only=True)
    product_gtin = serializers.CharField(source="batch.product.gtin", read_only=True)
    
    # Calculated fields
    effective_manufacturing_date = serializers.ReadOnlyField()
    effective_expiry_date = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    is_shipped = serializers.ReadOnlyField()
    is_delivered = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = m.Pack
        fields = [
            "id",
            "batch",
            "batch_lot_number",
            "product_name",
            "product_gtin",
            "serial_number",
            "pack_size",
            "pack_type",
            "manufacturing_date",
            "expiry_date",
            "effective_manufacturing_date",
            "effective_expiry_date",
            "status",
            "location",
            "warehouse_section",
            "quality_control_notes",
            "quality_control_passed",
            "regulatory_code",
            "customer_reference",
            "shipped_date",
            "delivered_date",
            "tracking_number",
            "is_expired",
            "days_until_expiry",
            "is_shipped",
            "is_delivered",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]
    
    def validate_serial_number(self, value):
        """Validate serial number uniqueness."""
        # Check uniqueness (excluding current instance if updating)
        queryset = m.Pack.objects.filter(serial_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A pack with this serial number already exists.")
        
        return value
    
    def validate(self, attrs):
        """Validate pack data."""
        manufacturing_date = attrs.get("manufacturing_date")
        expiry_date = attrs.get("expiry_date")
        shipped_date = attrs.get("shipped_date")
        delivered_date = attrs.get("delivered_date")
        
        # Validate date range if both dates are provided
        if manufacturing_date and expiry_date and expiry_date <= manufacturing_date:
            raise serializers.ValidationError({
                "expiry_date": "Pack expiry date must be after manufacturing date."
            })
        
        # Validate shipping dates
        if shipped_date and delivered_date and delivered_date < shipped_date:
            raise serializers.ValidationError({
                "delivered_date": "Delivery date must be after shipping date."
            })
        
        # Validate pack size
        pack_size = attrs.get("pack_size")
        if pack_size is not None and pack_size <= 0:
            raise serializers.ValidationError({
                "pack_size": "Pack size must be greater than zero."
            })
        
        # Validate batch exists and is active
        batch = attrs.get("batch")
        if batch and batch.status not in ["active", "released"]:
            raise serializers.ValidationError({
                "batch": "Cannot create pack for inactive or expired batch."
            })
        
        return attrs


class PackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new packs."""
    
    # Related fields from batch and product
    batch_lot_number = serializers.CharField(source="batch.lot_number", read_only=True)
    product_name = serializers.CharField(source="batch.product.name", read_only=True)
    product_gtin = serializers.CharField(source="batch.product.gtin", read_only=True)
    
    # Calculated fields
    effective_manufacturing_date = serializers.ReadOnlyField()
    effective_expiry_date = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    is_shipped = serializers.ReadOnlyField()
    is_delivered = serializers.ReadOnlyField()
    
    class Meta:
        model = m.Pack
        fields = [
            "id",
            "batch",
            "batch_lot_number",
            "product_name",
            "product_gtin",
            "serial_number",
            "pack_size",
            "pack_type",
            "manufacturing_date",
            "expiry_date",
            "effective_manufacturing_date",
            "effective_expiry_date",
            "status",
            "location",
            "warehouse_section",
            "quality_control_notes",
            "quality_control_passed",
            "regulatory_code",
            "customer_reference",
            "shipped_date",
            "delivered_date",
            "tracking_number",
            "is_expired",
            "days_until_expiry",
            "is_shipped",
            "is_delivered",
            "created_at",
        ]
        read_only_fields = [
            "id", 
            "created_at", 
            "effective_manufacturing_date",
            "effective_expiry_date",
            "is_expired", 
            "days_until_expiry", 
            "is_shipped", 
            "is_delivered"
        ]
    
    def validate_serial_number(self, value):
        """Validate serial number uniqueness."""
        if m.Pack.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("A pack with this serial number already exists.")
        
        return value
    
    def validate(self, attrs):
        """Validate pack data."""
        manufacturing_date = attrs.get("manufacturing_date")
        expiry_date = attrs.get("expiry_date")
        shipped_date = attrs.get("shipped_date")
        delivered_date = attrs.get("delivered_date")
        
        # Validate date range if both dates are provided
        if manufacturing_date and expiry_date and expiry_date <= manufacturing_date:
            raise serializers.ValidationError({
                "expiry_date": "Pack expiry date must be after manufacturing date."
            })
        
        # Validate shipping dates
        if shipped_date and delivered_date and delivered_date < shipped_date:
            raise serializers.ValidationError({
                "delivered_date": "Delivery date must be after shipping date."
            })
        
        # Validate pack size
        pack_size = attrs.get("pack_size")
        if pack_size is not None and pack_size <= 0:
            raise serializers.ValidationError({
                "pack_size": "Pack size must be greater than zero."
            })
        
        # Validate batch exists and is active
        batch = attrs.get("batch")
        if batch and batch.status not in ["active", "released"]:
            raise serializers.ValidationError({
                "batch": "Cannot create pack for inactive or expired batch."
            })
        
        return attrs
