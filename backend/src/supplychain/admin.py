from django.contrib import admin

import supplychain.models as m


@admin.register(m.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "active_role", "created_at")
    search_fields = ("user__username", "user__email")


@admin.register(m.RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "granted_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(m.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "gtin",
        "form",
        "strength",
        "manufacturer",
        "status",
        "storage_range_display",
        "created_at",
    )
    list_filter = ("status", "form", "manufacturer", "created_at")
    search_fields = ("name", "gtin", "manufacturer", "ndc", "description")
    readonly_fields = ("storage_range_display", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {"fields": ("gtin", "name", "description", "status")}),
        (
            "Product Details",
            {"fields": ("form", "strength", "manufacturer", "ndc", "approval_number")},
        ),
        (
            "Storage Requirements",
            {
                "fields": (
                    "storage_temp_min",
                    "storage_temp_max",
                    "storage_humidity_min",
                    "storage_humidity_max",
                    "storage_range_display",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted products in admin."""
        return self.model.all_objects.get_queryset()


@admin.register(m.Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "lot_number",
        "product",
        "manufacturing_date",
        "expiry_date",
        "quantity_produced",
        "manufacturing_location",
        "status",
        "quality_control_passed",
        "is_expired",
        "days_until_expiry",
        "created_at",
    )
    list_filter = (
        "status",
        "quality_control_passed",
        "manufacturing_date",
        "expiry_date",
        "manufacturing_location",
        "product__name",
        "created_at",
    )
    search_fields = (
        "lot_number",
        "product__name",
        "product__gtin",
        "manufacturing_location",
        "manufacturing_facility",
        "quality_control_notes",
        "supplier_batch_number",
    )
    readonly_fields = (
        "is_expired",
        "days_until_expiry",
        "age_in_days",
        "shelf_life_remaining_percent",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Information", {"fields": ("product", "lot_number", "status")}),
        (
            "Production Details",
            {
                "fields": (
                    "manufacturing_date",
                    "expiry_date",
                    "quantity_produced",
                    "batch_size",
                    "manufacturing_location",
                    "manufacturing_facility",
                )
            },
        ),
        (
            "Quality Control",
            {"fields": ("quality_control_passed", "quality_control_notes")},
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "supplier_batch_number",
                    "regulatory_approval_number",
                    "certificate_of_analysis",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Calculated Fields",
            {
                "fields": (
                    "is_expired",
                    "days_until_expiry",
                    "age_in_days",
                    "shelf_life_remaining_percent",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted batches in admin."""
        return self.model.all_objects.select_related("product").get_queryset()


@admin.register(m.Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = (
        "serial_number",
        "batch",
        "product_name",
        "pack_size",
        "pack_type",
        "status",
        "location",
        "effective_expiry_date",
        "is_expired",
        "quality_control_passed",
        "is_shipped",
        "is_delivered",
        "created_at",
    )
    list_filter = (
        "status",
        "pack_type",
        "quality_control_passed",
        "location",
        "batch__product__name",
        "batch__status",
        "shipped_date",
        "delivered_date",
        "created_at",
    )
    search_fields = (
        "serial_number",
        "batch__lot_number",
        "batch__product__name",
        "batch__product__gtin",
        "location",
        "warehouse_section",
        "customer_reference",
        "tracking_number",
        "regulatory_code",
    )
    readonly_fields = (
        "effective_manufacturing_date",
        "effective_expiry_date",
        "is_expired",
        "days_until_expiry",
        "product_name",
        "product_gtin",
        "lot_number",
        "is_shipped",
        "is_delivered",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("batch", "serial_number", "pack_size", "pack_type", "status")},
        ),
        (
            "Related Information",
            {
                "fields": ("product_name", "product_gtin", "lot_number"),
                "classes": ("collapse",),
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "manufacturing_date",
                    "expiry_date",
                    "effective_manufacturing_date",
                    "effective_expiry_date",
                    "is_expired",
                    "days_until_expiry",
                )
            },
        ),
        ("Location", {"fields": ("location", "warehouse_section")}),
        (
            "Quality Control",
            {"fields": ("quality_control_passed", "quality_control_notes")},
        ),
        (
            "Shipping Information",
            {
                "fields": (
                    "shipped_date",
                    "delivered_date",
                    "tracking_number",
                    "is_shipped",
                    "is_delivered",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("regulatory_code", "customer_reference"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted packs in admin."""
        return self.model.all_objects.select_related("batch__product").get_queryset()

    def product_name(self, obj):
        """Display product name through batch relationship."""
        return obj.batch.product.name

    product_name.short_description = "Product"
    product_name.admin_order_field = "batch__product__name"


class ShipmentPackInline(admin.TabularInline):
    """Inline admin for ShipmentPack model."""

    model = m.ShipmentPack
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("pack", "quantity_shipped", "notes", "created_at")

    def get_queryset(self, request):
        """Include related pack information."""
        return super().get_queryset(request).select_related("pack__batch__product")


@admin.register(m.Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "status",
        "carrier",
        "service_type",
        "origin_name",
        "destination_name",
        "pack_count",
        "shipped_date",
        "estimated_delivery_date",
        "is_delivered",
        "created_at",
    )
    list_filter = (
        "status",
        "carrier",
        "service_type",
        "temperature_requirement",
        "special_handling_required",
        "origin_state",
        "destination_state",
        "shipped_date",
        "estimated_delivery_date",
        "created_at",
    )
    search_fields = (
        "tracking_number",
        "origin_name",
        "destination_name",
        "origin_city",
        "destination_city",
        "billing_reference",
        "notes",
        "packs__serial_number",
        "packs__batch__lot_number",
        "packs__batch__product__name",
    )
    readonly_fields = (
        "pack_count",
        "total_pack_size",
        "origin_address",
        "destination_address",
        "is_delivered",
        "is_in_transit",
        "is_completed",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("tracking_number", "status", "carrier", "service_type")},
        ),
        (
            "Origin",
            {
                "fields": (
                    "origin_name",
                    "origin_address_line1",
                    "origin_address_line2",
                    "origin_city",
                    "origin_state",
                    "origin_postal_code",
                    "origin_country",
                    "origin_address",
                )
            },
        ),
        (
            "Destination",
            {
                "fields": (
                    "destination_name",
                    "destination_address_line1",
                    "destination_address_line2",
                    "destination_city",
                    "destination_state",
                    "destination_postal_code",
                    "destination_country",
                    "destination_address",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "shipped_date",
                    "estimated_delivery_date",
                    "actual_delivery_date",
                )
            },
        ),
        (
            "Requirements",
            {
                "fields": (
                    "temperature_requirement",
                    "special_handling_required",
                    "special_instructions",
                )
            },
        ),
        (
            "Cost and Billing",
            {
                "fields": ("shipping_cost", "currency", "billing_reference"),
                "classes": ("collapse",),
            },
        ),
        (
            "Pack Information",
            {"fields": ("pack_count", "total_pack_size"), "classes": ("collapse",)},
        ),
        (
            "Status Information",
            {
                "fields": ("is_delivered", "is_in_transit", "is_completed"),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Information",
            {"fields": ("notes", "external_tracking_url"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [ShipmentPackInline]

    def get_queryset(self, request):
        """Include soft-deleted shipments in admin."""
        return self.model.all_objects.prefetch_related("packs").get_queryset()


@admin.register(m.ShipmentPack)
class ShipmentPackAdmin(admin.ModelAdmin):
    list_display = (
        "shipment_tracking_number",
        "pack_serial_number",
        "product_name",
        "batch_lot_number",
        "quantity_shipped",
        "created_at",
    )
    list_filter = (
        "shipment__status",
        "shipment__carrier",
        "pack__pack_type",
        "pack__batch__product__name",
        "created_at",
    )
    search_fields = (
        "shipment__tracking_number",
        "pack__serial_number",
        "pack__batch__lot_number",
        "pack__batch__product__name",
        "notes",
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        """Include related information."""
        return (
            super()
            .get_queryset(request)
            .select_related("shipment", "pack__batch__product")
        )

    def shipment_tracking_number(self, obj):
        """Display shipment tracking number."""
        return obj.shipment.tracking_number

    shipment_tracking_number.short_description = "Shipment"
    shipment_tracking_number.admin_order_field = "shipment__tracking_number"

    def pack_serial_number(self, obj):
        """Display pack serial number."""
        return obj.pack.serial_number

    pack_serial_number.short_description = "Pack"
    pack_serial_number.admin_order_field = "pack__serial_number"

    def product_name(self, obj):
        """Display product name through pack->batch relationship."""
        return obj.pack.batch.product.name

    product_name.short_description = "Product"
    product_name.admin_order_field = "pack__batch__product__name"

    def batch_lot_number(self, obj):
        """Display batch lot number through pack relationship."""
        return obj.pack.batch.lot_number

    batch_lot_number.short_description = "Batch"
    batch_lot_number.admin_order_field = "pack__batch__lot_number"


@admin.register(m.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "event_type",
        "entity_type",
        "entity_display_name",
        "severity",
        "user_username",
        "location",
        "is_critical",
        "is_alert",
        "created_at",
    )
    list_filter = (
        "event_type",
        "entity_type",
        "severity",
        "timestamp",
        "user",
        "location",
        "created_at",
    )
    search_fields = (
        "description",
        "location",
        "user__username",
        "user__first_name",
        "user__last_name",
        "metadata",
        "ip_address",
    )
    readonly_fields = (
        "timestamp",
        "entity_display_name",
        "is_critical",
        "is_alert",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Event Information",
            {
                "fields": (
                    "event_type",
                    "entity_type",
                    "entity_id",
                    "entity_display_name",
                    "timestamp",
                )
            },
        ),
        ("Description", {"fields": ("description", "severity", "location")}),
        (
            "User Context",
            {"fields": ("user", "ip_address", "user_agent"), "classes": ("collapse",)},
        ),
        ("Metadata", {"fields": ("metadata", "system_info"), "classes": ("collapse",)}),
        ("Status", {"fields": ("is_critical", "is_alert"), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    date_hierarchy = "timestamp"
    ordering = ["-timestamp", "-id"]

    def get_queryset(self, request):
        """Include soft-deleted events in admin and optimize queries."""
        return self.model.all_objects.select_related("user", "content_type").all()

    def user_username(self, obj):
        """Display username of the user who triggered the event."""
        return obj.user.username if obj.user else "System"

    user_username.short_description = "User"
    user_username.admin_order_field = "user__username"

    def has_add_permission(self, request):
        """Allow adding events through admin."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow changing events (for corrections)."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion for superusers."""
        return request.user.is_superuser
