from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from .. import models as m


ACTIVE_SHIPMENT_STATUSES = [
    "pending",
    "confirmed",
    "picked_up",
    "in_transit",
    "out_for_delivery",
]


def _validate_pack_ids_for_shipment(pack_ids, shipment_instance=None):
    """Validate pack IDs for shipment create/update operations."""
    if not pack_ids:
        raise serializers.ValidationError(
            "At least one pack must be included in the shipment."
        )

    existing_packs = m.Pack.objects.filter(id__in=pack_ids, deleted_at__isnull=True)
    if existing_packs.count() != len(set(pack_ids)):
        raise serializers.ValidationError("One or more pack IDs are invalid or deleted.")

    active_shipment_packs = m.ShipmentPack.objects.filter(
        pack_id__in=pack_ids,
        shipment__status__in=ACTIVE_SHIPMENT_STATUSES,
    )

    if shipment_instance is not None:
        active_shipment_packs = active_shipment_packs.exclude(shipment=shipment_instance)

    blocked_pack_ids = list(active_shipment_packs.values_list("pack_id", flat=True).distinct())
    if blocked_pack_ids:
        raise serializers.ValidationError(
            f"Packs {blocked_pack_ids} are already in active shipments."
        )

    return pack_ids


class ShipmentPackSerializer(serializers.ModelSerializer):
    """Serializer for ShipmentPack intermediate model."""

    # Pack information
    pack_serial_number = serializers.CharField(
        source="pack.serial_number", read_only=True
    )
    pack_size = serializers.IntegerField(source="pack.pack_size", read_only=True)
    pack_type = serializers.CharField(source="pack.pack_type", read_only=True)
    batch_lot_number = serializers.CharField(
        source="pack.batch.lot_number", read_only=True
    )
    product_name = serializers.CharField(
        source="pack.batch.product.name", read_only=True
    )
    product_gtin = serializers.CharField(
        source="pack.batch.product.gtin", read_only=True
    )

    class Meta:
        model = m.ShipmentPack
        fields = [
            "id",
            "pack",
            "pack_serial_number",
            "pack_size",
            "pack_type",
            "batch_lot_number",
            "product_name",
            "product_gtin",
            "quantity_shipped",
            "notes",
            "created_at",
        ]


class ShipmentListSerializer(serializers.ModelSerializer):
    """Serializer for shipment list view with essential fields."""

    # Calculated fields
    is_delivered = serializers.ReadOnlyField()
    is_in_transit = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    pack_count = serializers.ReadOnlyField()
    total_pack_size = serializers.ReadOnlyField()
    origin_address = serializers.ReadOnlyField()
    destination_address = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    # Summary information about packs
    pack_summary = serializers.SerializerMethodField()

    class Meta:
        model = m.Shipment
        fields = [
            "id",
            "tracking_number",
            "status",
            "carrier",
            "service_type",
            "origin_name",
            "origin_address",
            "destination_name",
            "destination_address",
            "shipped_date",
            "estimated_delivery_date",
            "actual_delivery_date",
            "temperature_requirement",
            "shipping_cost",
            "currency",
            "pack_count",
            "total_pack_size",
            "pack_summary",
            "is_delivered",
            "is_in_transit",
            "is_completed",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def get_pack_summary(self, obj):
        """Get a summary of packs in the shipment."""
        packs = obj.packs.select_related("batch__product").all()
        products = {}

        for pack in packs:
            product_name = pack.batch.product.name
            if product_name in products:
                products[product_name] += 1
            else:
                products[product_name] = 1

        return [{"product": name, "count": count} for name, count in products.items()]


class ShipmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for shipment detail view with all fields."""

    # Calculated fields
    is_delivered = serializers.ReadOnlyField()
    is_in_transit = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    pack_count = serializers.ReadOnlyField()
    total_pack_size = serializers.ReadOnlyField()
    origin_address = serializers.ReadOnlyField()
    destination_address = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    # Related packs information
    shipment_packs = ShipmentPackSerializer(many=True, read_only=True)

    class Meta:
        model = m.Shipment
        fields = [
            "id",
            "tracking_number",
            "status",
            "carrier",
            "service_type",
            "origin_name",
            "origin_address_line1",
            "origin_address_line2",
            "origin_city",
            "origin_state",
            "origin_postal_code",
            "origin_country",
            "origin_address",
            "destination_name",
            "destination_address_line1",
            "destination_address_line2",
            "destination_city",
            "destination_state",
            "destination_postal_code",
            "destination_country",
            "destination_address",
            "shipped_date",
            "estimated_delivery_date",
            "actual_delivery_date",
            "temperature_requirement",
            "special_handling_required",
            "special_instructions",
            "shipping_cost",
            "currency",
            "billing_reference",
            "notes",
            "external_tracking_url",
            "pack_count",
            "total_pack_size",
            "shipment_packs",
            "is_delivered",
            "is_in_transit",
            "is_completed",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def validate_tracking_number(self, value):
        """Validate tracking number uniqueness."""
        # Check uniqueness (excluding current instance if updating)
        queryset = m.Shipment.objects.filter(tracking_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A shipment with this tracking number already exists."
            )

        return value

    def validate(self, attrs):
        """Validate shipment data."""
        shipped_date = attrs.get("shipped_date")
        estimated_delivery_date = attrs.get("estimated_delivery_date")
        actual_delivery_date = attrs.get("actual_delivery_date")

        # Validate date relationships
        if (
            shipped_date
            and estimated_delivery_date
            and estimated_delivery_date < shipped_date
        ):
            raise serializers.ValidationError(
                {
                    "estimated_delivery_date": "Estimated delivery date must be after shipped date."
                }
            )

        if (
            shipped_date
            and actual_delivery_date
            and actual_delivery_date < shipped_date
        ):
            raise serializers.ValidationError(
                {
                    "actual_delivery_date": "Actual delivery date must be after shipped date."
                }
            )

        # Validate shipping cost
        shipping_cost = attrs.get("shipping_cost")
        if shipping_cost is not None and shipping_cost < 0:
            raise serializers.ValidationError(
                {"shipping_cost": "Shipping cost cannot be negative."}
            )

        return attrs


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new shipments."""

    # Pack IDs for creating the many-to-many relationship
    pack_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="List of pack IDs to include in the shipment",
    )

    # Calculated fields
    is_delivered = serializers.ReadOnlyField()
    is_in_transit = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    pack_count = serializers.ReadOnlyField()
    total_pack_size = serializers.ReadOnlyField()
    origin_address = serializers.ReadOnlyField()
    destination_address = serializers.ReadOnlyField()

    # Related packs information
    shipment_packs = ShipmentPackSerializer(many=True, read_only=True)

    class Meta:
        model = m.Shipment
        fields = [
            "id",
            "tracking_number",
            "status",
            "carrier",
            "service_type",
            "origin_name",
            "origin_address_line1",
            "origin_address_line2",
            "origin_city",
            "origin_state",
            "origin_postal_code",
            "origin_country",
            "origin_address",
            "destination_name",
            "destination_address_line1",
            "destination_address_line2",
            "destination_city",
            "destination_state",
            "destination_postal_code",
            "destination_country",
            "destination_address",
            "shipped_date",
            "estimated_delivery_date",
            "actual_delivery_date",
            "temperature_requirement",
            "special_handling_required",
            "special_instructions",
            "shipping_cost",
            "currency",
            "billing_reference",
            "notes",
            "external_tracking_url",
            "pack_ids",
            "pack_count",
            "total_pack_size",
            "shipment_packs",
            "is_delivered",
            "is_in_transit",
            "is_completed",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "pack_count",
            "total_pack_size",
            "is_delivered",
            "is_in_transit",
            "is_completed",
        ]

    def validate_tracking_number(self, value):
        """Validate tracking number uniqueness."""
        if m.Shipment.objects.filter(tracking_number=value).exists():
            raise serializers.ValidationError(
                "A shipment with this tracking number already exists."
            )

        return value

    def validate_pack_ids(self, value):
        """Validate pack IDs."""
        return _validate_pack_ids_for_shipment(value)

    def validate(self, attrs):
        """Validate shipment data."""
        shipped_date = attrs.get("shipped_date")
        estimated_delivery_date = attrs.get("estimated_delivery_date")
        actual_delivery_date = attrs.get("actual_delivery_date")

        # Validate date relationships
        if (
            shipped_date
            and estimated_delivery_date
            and estimated_delivery_date < shipped_date
        ):
            raise serializers.ValidationError(
                {
                    "estimated_delivery_date": "Estimated delivery date must be after shipped date."
                }
            )

        if (
            shipped_date
            and actual_delivery_date
            and actual_delivery_date < shipped_date
        ):
            raise serializers.ValidationError(
                {
                    "actual_delivery_date": "Actual delivery date must be after shipped date."
                }
            )

        # Validate shipping cost
        shipping_cost = attrs.get("shipping_cost")
        if shipping_cost is not None and shipping_cost < 0:
            raise serializers.ValidationError(
                {"shipping_cost": "Shipping cost cannot be negative."}
            )

        return attrs

    def create(self, validated_data):
        """Create shipment with associated packs."""
        pack_ids = validated_data.pop("pack_ids")
        shipment = m.Shipment.objects.create(**validated_data)

        # Create ShipmentPack relationships
        for pack_id in pack_ids:
            m.ShipmentPack.objects.create(
                shipment=shipment,
                pack_id=pack_id,
                quantity_shipped=1,  # Default quantity
            )

        return shipment


class ShipmentUpdateSerializer(ShipmentDetailSerializer):
    """Serializer for updating shipments, including pack relationships."""

    pack_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Optional list of pack IDs to replace shipment packs",
    )

    class Meta(ShipmentDetailSerializer.Meta):
        fields = ShipmentDetailSerializer.Meta.fields + ["pack_ids"]

    def validate_pack_ids(self, value):
        """Validate pack IDs for shipment update."""
        return _validate_pack_ids_for_shipment(value, shipment_instance=self.instance)

    @staticmethod
    def _reset_pack_if_unassigned(pack):
        """Reset pack shipping state if it is no longer in active shipments."""
        has_other_active_shipments = pack.pack_shipments.filter(
            shipment__status__in=["picked_up", "in_transit", "out_for_delivery", "delivered"]
        ).exists()

        if (
            not has_other_active_shipments
            and pack.status in ["shipped", "delivered"]
        ):
            pack.status = "active"
            pack.shipped_date = None
            pack.delivered_date = None
            pack.save()

    def _sync_shipment_packs(self, shipment, pack_ids):
        """Replace shipment packs with the provided IDs."""
        requested_pack_ids = set(pack_ids)
        existing_shipment_packs = {
            shipment_pack.pack_id: shipment_pack
            for shipment_pack in shipment.shipment_packs.select_related("pack").all()
        }

        remove_ids = set(existing_shipment_packs.keys()) - requested_pack_ids
        add_ids = requested_pack_ids - set(existing_shipment_packs.keys())

        for pack_id in remove_ids:
            shipment_pack = existing_shipment_packs[pack_id]
            pack = shipment_pack.pack
            shipment_pack.delete()
            self._reset_pack_if_unassigned(pack)

        for pack_id in add_ids:
            m.ShipmentPack.objects.create(
                shipment=shipment,
                pack_id=pack_id,
                quantity_shipped=1,
            )

    def update(self, instance, validated_data):
        """Update shipment fields and optionally replace related packs."""
        pack_ids = validated_data.pop("pack_ids", None)

        with transaction.atomic():
            shipment = super().update(instance, validated_data)
            if pack_ids is not None:
                self._sync_shipment_packs(shipment, pack_ids)

        return shipment
