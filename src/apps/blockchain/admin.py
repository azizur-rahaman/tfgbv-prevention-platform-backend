from django.contrib import admin
from .models import ForensicLog


@admin.register(ForensicLog)
class ForensicLogAdmin(admin.ModelAdmin):
    list_display = (
        "block_number",
        "event_type",
        "evidence",
        "actor_role",
        "timestamp",
        "block_hash",
    )
    readonly_fields = (
        "block_number",
        "previous_hash",
        "block_hash",
        "timestamp",
    )
    ordering = ("block_number",)