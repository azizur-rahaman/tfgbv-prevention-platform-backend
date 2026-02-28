from rest_framework import serializers
from apps.report.models import Report
from apps.evidence.models import Evidence


class ReportSubmitSerializer(serializers.Serializer):
    """
    Validate report submission from mobile app (multipart/form-data).
    evidence_vault_ids: JSON array of UUID strings, e.g. '["uuid1", "uuid2"]'
    """

    evidence_vault_ids = serializers.CharField(
        help_text="JSON array of evidence vault_id (UUIDs) in the vault to attach, e.g. [\"uuid1\", \"uuid2\"]",
    )
    testimonial_text = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50000,
    )
    testimonial_voice = serializers.FileField(required=False, allow_null=True)
    testimonial_video = serializers.FileField(required=False, allow_null=True)
    digital_signature = serializers.CharField(allow_blank=False, max_length=10000)
    signature_algorithm = serializers.CharField(
        required=False,
        allow_blank=True,
        default="RSA-SHA256",
        max_length=50,
    )

    def validate_evidence_vault_ids(self, value):
        import json
        try:
            ids = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError(
                "evidence_vault_ids must be a JSON array of UUID strings."
            )
        if not isinstance(ids, list):
            raise serializers.ValidationError(
                "evidence_vault_ids must be a JSON array."
            )
        for i, v in enumerate(ids):
            if not isinstance(v, str):
                raise serializers.ValidationError(
                    f"evidence_vault_ids[{i}] must be a string UUID."
                )
            try:
                from uuid import UUID
                UUID(v)
            except ValueError:
                raise serializers.ValidationError(
                    f"evidence_vault_ids[{i}] is not a valid UUID."
                )
        return ids


class ReportListSerializer(serializers.ModelSerializer):
    evidence_count = serializers.SerializerMethodField()
    has_voice = serializers.SerializerMethodField()
    has_video = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "created_at",
            "testimonial_text",
            "has_voice",
            "has_video",
            "signature_algorithm",
            "evidence_count",
        )

    def get_evidence_count(self, obj):
        return obj.evidences.count()

    def get_has_voice(self, obj):
        return bool(obj.testimonial_voice_path)

    def get_has_video(self, obj):
        return bool(obj.testimonial_video_path)


class ReportDetailSerializer(serializers.ModelSerializer):
    evidence_vault_ids = serializers.SerializerMethodField()
    has_voice = serializers.SerializerMethodField()
    has_video = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "reporter",
            "created_at",
            "updated_at",
            "testimonial_text",
            "testimonial_voice_path",
            "testimonial_video_path",
            "has_voice",
            "has_video",
            "signature_algorithm",
            "evidence_vault_ids",
        )

    def get_evidence_vault_ids(self, obj):
        return [str(ev.vault_id) for ev in obj.evidences.all()]

    def get_has_voice(self, obj):
        return bool(obj.testimonial_voice_path)

    def get_has_video(self, obj):
        return bool(obj.testimonial_video_path)
