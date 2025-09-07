from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .. import models as m

User = get_user_model()


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for Event list view with essential information and related entity details.
    """

    # Display fields for better readability
    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    entity_type_display = serializers.CharField(
        source="get_entity_type_display", read_only=True
    )
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )

    # User information
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_full_name = serializers.SerializerMethodField()

    # Entity information
    entity_display_name = serializers.ReadOnlyField()
    entity_info = serializers.SerializerMethodField()

    # Computed fields
    is_critical = serializers.ReadOnlyField()
    is_alert = serializers.ReadOnlyField()

    # Blockchain integrity fields
    is_blockchain_anchored = serializers.ReadOnlyField()
    blockchain_explorer_url = serializers.ReadOnlyField()

    class Meta:
        model = m.Event
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "entity_type",
            "entity_type_display",
            "entity_id",
            "entity_display_name",
            "entity_info",
            "timestamp",
            "description",
            "severity",
            "severity_display",
            "location",
            "user",
            "user_username",
            "user_full_name",
            "is_critical",
            "is_alert",
            "blockchain_tx_hash",
            "blockchain_block_number",
            "integrity_status",
            "event_hash",
            "is_blockchain_anchored",
            "blockchain_explorer_url",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "timestamp",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def get_user_full_name(self, obj):
        """Get the full name of the user who triggered the event."""
        if obj.user:
            return (
                f"{obj.user.first_name} {obj.user.last_name}".strip()
                or obj.user.username
            )
        return None

    def get_entity_info(self, obj):
        """Get detailed information about the related entity."""
        return obj.get_related_entity_info()


class EventDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Event detail view with complete information including metadata.
    """

    # Display fields for better readability
    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    entity_type_display = serializers.CharField(
        source="get_entity_type_display", read_only=True
    )
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )

    # User information
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True)

    # Entity information
    entity_display_name = serializers.ReadOnlyField()
    entity_info = serializers.SerializerMethodField()

    # Computed fields
    is_critical = serializers.ReadOnlyField()
    is_alert = serializers.ReadOnlyField()

    # Blockchain integrity fields
    is_blockchain_anchored = serializers.ReadOnlyField()
    blockchain_explorer_url = serializers.ReadOnlyField()

    # Related entity details (when available)
    related_product = serializers.SerializerMethodField()
    related_batch = serializers.SerializerMethodField()
    related_pack = serializers.SerializerMethodField()
    related_shipment = serializers.SerializerMethodField()

    class Meta:
        model = m.Event
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "entity_type",
            "entity_type_display",
            "entity_id",
            "entity_display_name",
            "entity_info",
            "timestamp",
            "description",
            "metadata",
            "severity",
            "severity_display",
            "location",
            "user",
            "user_username",
            "user_full_name",
            "user_email",
            "ip_address",
            "user_agent",
            "system_info",
            "is_critical",
            "is_alert",
            "blockchain_tx_hash",
            "blockchain_block_number",
            "integrity_status",
            "event_hash",
            "is_blockchain_anchored",
            "blockchain_explorer_url",
            "related_product",
            "related_batch",
            "related_pack",
            "related_shipment",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "timestamp",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def get_user_full_name(self, obj):
        """Get the full name of the user who triggered the event."""
        if obj.user:
            return (
                f"{obj.user.first_name} {obj.user.last_name}".strip()
                or obj.user.username
            )
        return None

    def get_entity_info(self, obj):
        """Get detailed information about the related entity."""
        return obj.get_related_entity_info()

    def get_related_product(self, obj):
        """Get related product information if applicable."""
        if obj.entity_type == "product" and obj.content_object:
            return {
                "id": obj.content_object.id,
                "name": obj.content_object.name,
                "gtin": obj.content_object.gtin,
                "form": obj.content_object.form,
                "strength": obj.content_object.strength,
            }
        elif obj.entity_type in ["batch", "pack"] and obj.content_object:
            if hasattr(obj.content_object, "product"):
                product = obj.content_object.product
            elif hasattr(obj.content_object, "batch") and hasattr(
                obj.content_object.batch, "product"
            ):
                product = obj.content_object.batch.product
            else:
                return None

            return {
                "id": product.id,
                "name": product.name,
                "gtin": product.gtin,
                "form": product.form,
                "strength": product.strength,
            }
        return None

    def get_related_batch(self, obj):
        """Get related batch information if applicable."""
        if obj.entity_type == "batch" and obj.content_object:
            return {
                "id": obj.content_object.id,
                "lot_number": obj.content_object.lot_number,
                "manufacturing_date": obj.content_object.manufacturing_date,
                "expiry_date": obj.content_object.expiry_date,
                "status": obj.content_object.status,
                "quantity": obj.content_object.quantity,
            }
        elif (
            obj.entity_type == "pack"
            and obj.content_object
            and hasattr(obj.content_object, "batch")
        ):
            batch = obj.content_object.batch
            return {
                "id": batch.id,
                "lot_number": batch.lot_number,
                "manufacturing_date": batch.manufacturing_date,
                "expiry_date": batch.expiry_date,
                "status": batch.status,
                "quantity": batch.quantity,
            }
        return None

    def get_related_pack(self, obj):
        """Get related pack information if applicable."""
        if obj.entity_type == "pack" and obj.content_object:
            return {
                "id": obj.content_object.id,
                "serial_number": obj.content_object.serial_number,
                "pack_size": obj.content_object.pack_size,
                "pack_type": obj.content_object.pack_type,
                "status": obj.content_object.status,
                "location": obj.content_object.location,
            }
        return None

    def get_related_shipment(self, obj):
        """Get related shipment information if applicable."""
        if obj.entity_type == "shipment" and obj.content_object:
            return {
                "id": obj.content_object.id,
                "tracking_number": obj.content_object.tracking_number,
                "status": obj.content_object.status,
                "carrier": obj.content_object.carrier,
                "service_type": obj.content_object.service_type,
                "origin_name": obj.content_object.origin_name,
                "destination_name": obj.content_object.destination_name,
            }
        return None


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new events with validation.
    """

    class Meta:
        model = m.Event
        fields = [
            "event_type",
            "entity_type",
            "entity_id",
            "description",
            "metadata",
            "severity",
            "location",
            "user",
            "ip_address",
            "user_agent",
            "system_info",
        ]

    def validate(self, data):
        """Validate the event data."""
        # Validate that the entity exists
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")

        if entity_type and entity_id:
            # Map entity types to models
            entity_models = {
                "product": m.Product,
                "batch": m.Batch,
                "pack": m.Pack,
                "shipment": m.Shipment,
                "user": User,
            }

            if entity_type in entity_models:
                model_class = entity_models[entity_type]
                if not model_class.objects.filter(id=entity_id).exists():
                    raise serializers.ValidationError(
                        f"{entity_type.title()} with ID {entity_id} does not exist."
                    )

        return data

    def create(self, validated_data):
        """Create a new event with proper content type association."""
        entity_type = validated_data.get("entity_type")
        entity_id = validated_data.get("entity_id")

        # Set the content type for generic foreign key
        if entity_type and entity_id:
            entity_models = {
                "product": m.Product,
                "batch": m.Batch,
                "pack": m.Pack,
                "shipment": m.Shipment,
                "user": User,
            }

            if entity_type in entity_models:
                model_class = entity_models[entity_type]
                content_type = ContentType.objects.get_for_model(model_class)
                validated_data["content_type"] = content_type

        return super().create(validated_data)
