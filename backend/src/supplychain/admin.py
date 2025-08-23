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
