import hashlib
import uuid
from django.db import models
from django.conf import settings


class Evidence(models.Model):
    """
    The core forensic record.
    Stores the file reference, cryptographic hash, and all metadata
    required for Section 65B admissibility under Bangladesh Evidence Act 2022.
    """

    class EvidenceType(models.TextChoices):
        PHOTO = "photo", "Photograph"
        VIDEO = "video", "Video Recording"
        AUDIO = "audio", "Audio Recording"
        SCREENSHOT = "screenshot", "Screenshot"
        DOCUMENT = "document", "Document"

    class EvidenceStatus(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        VERIFIED = "verified", "Verified & Sealed"
        FLAGGED = "flagged", "Flagged - Integrity Issue"
        SUBMITTED = "submitted", "Submitted to Court"

    class HarmType(models.TextChoices):
        SEXTORTION = "sextortion", "Sextortion"
        IMAGE_ABUSE = "image_abuse", "Image-Based Abuse"
        DOXXING = "doxxing", "Doxxing"
        CYBERBULLYING = "cyberbullying", "Cyberbullying"
        HARASSMENT = "harassment", "Online Harassment"
        OTHER = "other", "Other"

    # ------------------------------------------------------------------ #
    # PRIMARY IDENTITY
    # ------------------------------------------------------------------ #
    vault_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique vault identifier. Used as the filename in BCC storage.",
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,           # Never delete evidence if user is deleted
        related_name="evidence_reports",
        help_text="The NID-verified user who submitted this evidence.",
    )

    # ------------------------------------------------------------------ #
    # CRYPTOGRAPHIC INTEGRITY  (Section 65B core requirement)
    # ------------------------------------------------------------------ #
    file_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash generated on the mobile device at point of capture.",
    )

    # BCC / MinIO storage path  e.g. "evidence/2025/01/uuid.jpg"
    storage_path = models.CharField(
        max_length=500,
        help_text="Path to the file inside the BCC National Data Center (MinIO).",
    )

    file_size_bytes = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes, recorded at upload.",
    )

    file_mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="MIME type e.g. image/jpeg, video/mp4",
    )

    # ------------------------------------------------------------------ #
    # ENCRYPTION & COMPRESSION  (Platform-lock fields)
    # ------------------------------------------------------------------ #
    is_encrypted = models.BooleanField(
        default=True,
        help_text="True if the stored file is AES-256-GCM encrypted.",
    )

    # A random 12-byte nonce is generated per file during encryption.
    # We store it here so we can decrypt later. It is NOT secret by itself.
    encryption_nonce = models.BinaryField(
        max_length=12,
        null=True,
        blank=True,
        help_text="AES-GCM nonce (IV) used during encryption. Unique per file.",
    )

    is_compressed = models.BooleanField(
        default=True,
        help_text="True if the file was gzip-compressed before encryption.",
    )

    # Size of the raw file BEFORE compression and encryption
    original_size_bytes = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Original uncompressed, unencrypted file size in bytes.",
    )

    # Size AFTER compression + encryption (what is actually stored in MinIO)
    stored_size_bytes = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Actual size stored in MinIO after compression and encryption.",
    )

    # ------------------------------------------------------------------ #
    # METADATA  (GPS + Time — legally critical for chain of custody)
    # ------------------------------------------------------------------ #
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS latitude at time of capture (hardware-level).",
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS longitude at time of capture (hardware-level).",
    )

    # Timestamp from the mobile device network time (NTP — not device clock)
    captured_at = models.DateTimeField(
        help_text="Network-synchronized timestamp from the mobile device at capture.",
    )

    # Timestamp when the Django backend received and stored the record
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Server-side timestamp when evidence was ingested into the vault.",
    )

    # ------------------------------------------------------------------ #
    # CLASSIFICATION
    # ------------------------------------------------------------------ #
    evidence_type = models.CharField(
        max_length=20,
        choices=EvidenceType.choices,
        default=EvidenceType.PHOTO,
    )

    harm_type = models.CharField(
        max_length=20,
        choices=HarmType.choices,
        default=HarmType.OTHER,
    )

    # Free-text description (optional, provided by victim)
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Victim's own description of the incident.",
    )

    # ------------------------------------------------------------------ #
    # STATUS & VERIFICATION
    # ------------------------------------------------------------------ #
    status = models.CharField(
        max_length=20,
        choices=EvidenceStatus.choices,
        default=EvidenceStatus.PENDING,
    )

    # Set to True once the Django backend re-hashes and confirms integrity
    is_hash_verified = models.BooleanField(
        default=False,
        help_text="True when server-side re-hash matches the mobile-submitted hash.",
    )

    # The officer or analyst who verified this evidence
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_evidence",
        help_text="Police officer or forensic analyst who verified this record.",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the verification was performed.",
    )

    # ------------------------------------------------------------------ #
    # DEVICE INFO  (for Section 65B 'device identification' requirement)
    # ------------------------------------------------------------------ #
    device_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Anonymised hardware identifier of the capture device.",
    )

    app_version = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Version of the Nirvhoy Flutter app used for capture.",
    )

    # ------------------------------------------------------------------ #
    # JURISDICTION (Phase 1 — Police upazila filtering)
    # ------------------------------------------------------------------ #
    assigned_upazila = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Upazila this evidence is assigned to. Police see only evidence for their assigned_upazila.",
    )

    # ------------------------------------------------------------------ #
    # VERDICT / DISPOSITION (Phase 1 — Judiciary)
    # ------------------------------------------------------------------ #
    class VerdictStatus(models.TextChoices):
        ADMITTED = "admitted", "Admitted"
        REJECTED = "rejected", "Rejected"
        UNDER_REVIEW = "under_review", "Under Review"

    verdict = models.CharField(
        max_length=20,
        choices=VerdictStatus.choices,
        null=True,
        blank=True,
        help_text="Court disposition recorded by judiciary.",
    )

    verdict_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the verdict was recorded.",
    )

    verdict_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verdicts_recorded",
        help_text="Judiciary user who recorded the verdict.",
    )

    class Meta:
        verbose_name = "Evidence Record"
        verbose_name_plural = "Evidence Records"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["reporter", "status"]),
            models.Index(fields=["file_hash"]),
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["assigned_upazila"]),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.vault_id} — {self.get_harm_type_display()}"

    def verify_hash(self) -> bool:
        """
        Placeholder for server-side re-hash verification.
        In production: download file from MinIO, compute SHA-256, compare.
        For prototype: just returns the stored verification state.
        """
        return self.is_hash_verified


class EvidencePurgeRequest(models.Model):
    """
    Victim request to delete evidence. BCC reviews and approves/denies.
    Deletion touches chain of custody; Phase 1 model for BCC dashboard (Phase 5).
    """

    class RequestStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"

    evidence = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        related_name="purge_requests",
        help_text="Evidence the victim wants purged.",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purge_requests_made",
        help_text="User (typically victim/reporter) who requested purge.",
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for purge request.",
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purge_requests_reviewed",
        help_text="BCC admin who reviewed.",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidence Purge Request"
        verbose_name_plural = "Evidence Purge Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Purge {self.evidence.vault_id} — {self.get_status_display()}"