from __future__ import annotations

from rest_framework import serializers

from .. import models as m
from ..validators import validate_temperature_range


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view with essential fields."""

    storage_range_display = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = m.Product
        fields = [
            "id",
            "gtin",
            "name",
            "form",
            "strength",
            "manufacturer",
            "status",
            "storage_range_display",
            "created_at",
            "updated_at",
            "is_deleted",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view with all fields."""

    storage_range_display = serializers.ReadOnlyField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = m.Product
        fields = [
            "id",
            "gtin",
            "name",
            "description",
            "form",
            "strength",
            "storage_temp_min",
            "storage_temp_max",
            "storage_humidity_min",
            "storage_humidity_max",
            "storage_range_display",
            "manufacturer",
            "ndc",
            "status",
            "approval_number",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def validate_gtin(self, value):
        """Validate GTIN format and uniqueness."""
        if not value.isdigit():
            raise serializers.ValidationError("GTIN must contain only digits.")

        if len(value) not in [8, 12, 13, 14]:
            raise serializers.ValidationError(
                "GTIN must be 8, 12, 13, or 14 digits long."
            )

        # Check uniqueness (excluding current instance if updating)
        queryset = m.Product.objects.filter(gtin=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A product with this GTIN already exists."
            )

        return value

    def validate(self, attrs):
        """Validate temperature and humidity ranges."""
        # Temperature range validation using custom validator
        temp_min = attrs.get("storage_temp_min") or (
            self.instance.storage_temp_min if self.instance else None
        )
        temp_max = attrs.get("storage_temp_max") or (
            self.instance.storage_temp_max if self.instance else None
        )

        try:
            validate_temperature_range(temp_min, temp_max)
        except serializers.ValidationError:
            raise

        # Humidity range validation
        humidity_min = attrs.get("storage_humidity_min")
        humidity_max = attrs.get("storage_humidity_max")

        if (
            humidity_min is not None
            and humidity_max is not None
            and humidity_min > humidity_max
        ):
            raise serializers.ValidationError(
                {
                    "storage_humidity_max": "Maximum humidity must be greater than minimum humidity."
                }
            )

        # Validate humidity bounds
        if humidity_min is not None and (humidity_min < 0 or humidity_min > 100):
            raise serializers.ValidationError(
                {"storage_humidity_min": "Humidity must be between 0% and 100%."}
            )

        if humidity_max is not None and (humidity_max < 0 or humidity_max > 100):
            raise serializers.ValidationError(
                {"storage_humidity_max": "Humidity must be between 0% and 100%."}
            )

        return attrs


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new products."""

    storage_range_display = serializers.ReadOnlyField()

    class Meta:
        model = m.Product
        fields = [
            "id",
            "gtin",
            "name",
            "description",
            "form",
            "strength",
            "storage_temp_min",
            "storage_temp_max",
            "storage_humidity_min",
            "storage_humidity_max",
            "storage_range_display",
            "manufacturer",
            "ndc",
            "status",
            "approval_number",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "storage_range_display"]

    def validate_gtin(self, value):
        """Validate GTIN format and uniqueness."""
        if not value.isdigit():
            raise serializers.ValidationError("GTIN must contain only digits.")

        if len(value) not in [8, 12, 13, 14]:
            raise serializers.ValidationError(
                "GTIN must be 8, 12, 13, or 14 digits long."
            )

        if m.Product.objects.filter(gtin=value).exists():
            raise serializers.ValidationError(
                "A product with this GTIN already exists."
            )

        return value

    def validate(self, attrs):
        """Validate temperature and humidity ranges."""
        # Temperature range validation using custom validator
        temp_min = attrs.get("storage_temp_min")
        temp_max = attrs.get("storage_temp_max")

        try:
            validate_temperature_range(temp_min, temp_max)
        except serializers.ValidationError:
            raise

        # Humidity range validation
        humidity_min = attrs.get("storage_humidity_min")
        humidity_max = attrs.get("storage_humidity_max")

        if (
            humidity_min is not None
            and humidity_max is not None
            and humidity_min > humidity_max
        ):
            raise serializers.ValidationError(
                {
                    "storage_humidity_max": "Maximum humidity must be greater than minimum humidity."
                }
            )

        # Validate humidity bounds
        if humidity_min is not None and (humidity_min < 0 or humidity_min > 100):
            raise serializers.ValidationError(
                {"storage_humidity_min": "Humidity must be between 0% and 100%."}
            )

        if humidity_max is not None and (humidity_max < 0 or humidity_max > 100):
            raise serializers.ValidationError(
                {"storage_humidity_max": "Humidity must be between 0% and 100%."}
            )

        return attrs
