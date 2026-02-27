from django.contrib import admin
from .models import Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "vault_id",
        "reporter",
        "harm_type",
        "evidence_type",
        "status",
        "is_hash_verified",
        "uploaded_at",
    )
    list_filter = ("status", "harm_type", "evidence_type", "is_hash_verified")
    search_fields = ("vault_id", "file_hash", "reporter__username")
    readonly_fields = (
        "vault_id",
        "file_hash",
        "uploaded_at",
        "storage_path",
        "is_hash_verified",
    )
    ordering = ("-uploaded_at",)