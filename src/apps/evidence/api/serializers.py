from rest_framework import serializers
from django.utils.dateparse import parse_datetime


class EvidenceUploadSerializer(serializers.Serializer):
    """
    Validates the multipart upload from the Flutter app.
    The mobile app sends the raw file + metadata as a multipart form.
    """

    # The actual file binary
    file = serializers.FileField(
        help_text="The raw captured file (photo/video/audio)."
    )

    # SHA-256 hash computed ON THE DEVICE before upload
    file_hash = serializers.CharField(
        max_length=64,
        min_length=64,
        help_text="SHA-256 hex digest computed on the mobile device.",
    )

    # Network-synchronized capture timestamp from mobile
    captured_at = serializers.DateTimeField(
        help_text="ISO 8601 datetime from network time (NTP) on device.",
    )

    evidence_type = serializers.ChoiceField(
        choices=["photo", "video", "audio", "screenshot", "document"],
        default="photo",
    )

    harm_type = serializers.ChoiceField(
        choices=[
            "sextortion",
            "image_abuse",
            "doxxing",
            "cyberbullying",
            "harassment",
            "other",
        ],
        default="other",
    )

    file_mime_type = serializers.CharField(
        max_length=100,
        default="image/jpeg",
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=2000,
    )

    device_id = serializers.CharField(
        required=False,
        allow_null=True,
        max_length=200,
    )

    app_version = serializers.CharField(
        required=False,
        allow_null=True,
        max_length=20,
    )

    def validate_file_hash(self, value):
        """Ensure hash is valid hex string."""
        try:
            int(value, 16)
        except ValueError:
            raise serializers.ValidationError(
                "file_hash must be a valid SHA-256 hex string."
            )
        return value.lower()