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
