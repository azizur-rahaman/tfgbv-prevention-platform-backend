from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AdminAuditLog


@admin.register(User)
class NirvhoyUserAdmin(UserAdmin):
    """
    Custom admin panel for the Nirvhoy User model.
    Extends Django's built-in UserAdmin so password hashing still works.
    """

    model = User

    # Columns shown in the user list view
    list_display = (
        "username",
        "email",
        "role",
        "nid_verified",
        "assigned_upazila",
        "is_active",
        "created_at",
    )

    list_filter = ("role", "nid_verified", "is_active", "assigned_upazila")

    search_fields = ("username", "email", "phone_number", "police_badge_id")

    ordering = ("-created_at",)

    # Add our custom fields into the detail/edit view
    fieldsets = UserAdmin.fieldsets + (
        (
            "NID & Forensic Identity",
            {
                "fields": (
                    "nid_hash",
                    "nid_verified",
                    "role",
                    "phone_number",
                )
            },
        ),
        (
            "Police / Officer Details",
            {
                "fields": (
                    "police_badge_id",
                    "assigned_upazila",
                )
            },
        ),
    )

    # Fields shown when CREATING a new user via admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "NID & Role",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "nid_hash",
                    "nid_verified",
                )
            },
        ),
    )

    # Make nid_hash read-only in admin (should only be set programmatically)
    readonly_fields = ("nid_hash", "created_at", "updated_at")


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "actor_user_id", "action", "target_user_id", "timestamp")
    list_filter = ("action",)
    search_fields = ("actor_user_id", "target_user_id")
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)