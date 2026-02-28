from django.contrib import admin
from .models import Evidence, EvidencePurgeRequest


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "vault_id",
        "reporter",
        "assigned_upazila",
        "harm_type",
        "evidence_type",
        "status",
        "verdict",
        "is_hash_verified",
        "uploaded_at",
    )
    list_filter = ("status", "harm_type", "evidence_type", "is_hash_verified", "verdict", "assigned_upazila")
    search_fields = ("vault_id", "file_hash", "reporter__username")
    readonly_fields = (
        "vault_id",
        "file_hash",
        "uploaded_at",
        "storage_path",
        "is_hash_verified",
    )
    ordering = ("-uploaded_at",)


@admin.register(EvidencePurgeRequest)
class EvidencePurgeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "evidence", "requested_by", "status", "reviewed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("evidence__vault_id", "requested_by__username")
    ordering = ("-created_at",)