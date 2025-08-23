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
        "created_at"
    )
    list_filter = ("status", "form", "manufacturer", "created_at")
    search_fields = ("name", "gtin", "manufacturer", "ndc", "description")
    readonly_fields = ("storage_range_display", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("gtin", "name", "description", "status")
        }),
        ("Product Details", {
            "fields": ("form", "strength", "manufacturer", "ndc", "approval_number")
        }),
        ("Storage Requirements", {
            "fields": (
                "storage_temp_min",
                "storage_temp_max",
                "storage_humidity_min",
                "storage_humidity_max",
                "storage_range_display"
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
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
        "created_at"
    )
    list_filter = (
        "status",
        "quality_control_passed",
        "manufacturing_date",
        "expiry_date",
        "manufacturing_location",
        "product__name",
        "created_at"
    )
    search_fields = (
        "lot_number",
        "product__name",
        "product__gtin",
        "manufacturing_location",
        "manufacturing_facility",
        "quality_control_notes",
        "supplier_batch_number"
    )
    readonly_fields = (
        "is_expired",
        "days_until_expiry",
        "age_in_days",
        "shelf_life_remaining_percent",
        "created_at",
        "updated_at"
    )

    fieldsets = (
        ("Basic Information", {
            "fields": ("product", "lot_number", "status")
        }),
        ("Production Details", {
            "fields": (
                "manufacturing_date",
                "expiry_date",
                "quantity_produced",
                "batch_size",
                "manufacturing_location",
                "manufacturing_facility"
            )
        }),
        ("Quality Control", {
            "fields": (
                "quality_control_passed",
                "quality_control_notes"
            )
        }),
        ("Additional Information", {
            "fields": (
                "supplier_batch_number",
                "regulatory_approval_number",
                "certificate_of_analysis"
            ),
            "classes": ("collapse",)
        }),
        ("Calculated Fields", {
            "fields": (
                "is_expired",
                "days_until_expiry",
                "age_in_days",
                "shelf_life_remaining_percent"
            ),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        """Include soft-deleted batches in admin."""
        return self.model.all_objects.select_related('product').get_queryset()
