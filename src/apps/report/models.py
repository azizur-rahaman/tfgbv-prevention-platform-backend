import uuid
from django.db import models
from django.conf import settings


class Report(models.Model):
    """
    User-submitted incident report linking vault evidence with testimonial
    (text, voice, or video) and digital signature. Stored in S3 and sealed in blockchain.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique report identifier.",
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incident_reports",
        help_text="User who filed this report.",
    )

    class ReportStatus(models.TextChoices):
        PENDING_POLICE = "pending_police", "Pending Police Confirmation"
        FORWARDED_TO_JUDICIARY = "forwarded_to_judiciary", "Forwarded to Judiciary"

    status = models.CharField(
        max_length=30,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING_POLICE,
        help_text="Workflow: pending_police → police confirm → forwarded_to_judiciary.",
    )

    # Evidence already in the vault — user supplies vault_ids (evidence hashes / refs)
    evidences = models.ManyToManyField(
        "evidence.Evidence",
        related_name="reports",
        blank=True,
        help_text="Evidence records in the vault that this report references.",
    )

    # Testimonial: text and/or media (voice, video) stored in S3
    testimonial_text = models.TextField(
        blank=True,
        help_text="Written testimonial about the incident.",
    )

    testimonial_voice_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="S3 path to voice testimonial file (e.g. report/testimonials/YYYY/MM/<id>_voice.*).",
    )

    testimonial_video_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="S3 path to video testimonial file.",
    )

    # Digital signature (e.g. base64 or hex from mobile)
    digital_signature = models.TextField(
        help_text="Digital signature payload (base64 or hex) from the reporting device.",
    )

    signature_algorithm = models.CharField(
        max_length=50,
        blank=True,
        default="RSA-SHA256",
        help_text="Algorithm used for the signature (e.g. RSA-SHA256).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Incident Report"
        verbose_name_plural = "Incident Reports"

    def __str__(self):
        return f"Report {self.id} by {self.reporter_id} ({self.created_at.date()})"
