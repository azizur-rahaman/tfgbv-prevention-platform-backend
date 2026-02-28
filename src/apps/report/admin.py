from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "created_at", "has_voice", "has_video")
    list_filter = ("created_at",)
    search_fields = ("id", "reporter__username", "testimonial_text")
    readonly_fields = ("id", "created_at", "updated_at")
    filter_horizontal = ("evidences",)
    ordering = ("-created_at",)

    def has_voice(self, obj):
        return bool(obj.testimonial_voice_path)

    has_voice.boolean = True

    def has_video(self, obj):
        return bool(obj.testimonial_video_path)

    has_video.boolean = True
