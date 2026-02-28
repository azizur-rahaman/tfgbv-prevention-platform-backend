"""
Submit an incident report: validate evidence refs, store testimonial files in S3,
and seal the report in the blockchain.
"""
import hashlib
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.report.models import Report
from apps.evidence.models import Evidence
from apps.blockchain.models import ForensicLog


def _report_content_hash(report: Report) -> str:
    """SHA-256 of report id + created_at for blockchain binding."""
    content = f"{report.id}{report.created_at.isoformat()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def submit_report(
    reporter,
    evidence_vault_ids: list,
    testimonial_text: str = "",
    testimonial_voice_file=None,
    testimonial_video_file=None,
    digital_signature: str = "",
    signature_algorithm: str = "RSA-SHA256",
) -> dict:
    """
    Create a report, upload optional voice/video to S3, link evidence, and seal in blockchain.

    - evidence_vault_ids: list of UUIDs (vault_id) of Evidence the user owns (reporter).
    - testimonial_voice_file: file-like (e.g. request.FILES['testimonial_voice']) or None.
    - testimonial_video_file: file-like or None.
    - digital_signature: required string (base64 or hex from mobile).

    Returns dict with report_id, block_number, and stored paths.
    Raises ValueError if vault_ids invalid or reporter doesn't own evidence.
    """
    if not digital_signature or not digital_signature.strip():
        raise ValueError("digital_signature is required.")

    # Resolve evidence: must exist and belong to reporter
    evidence_qs = Evidence.objects.filter(vault_id__in=evidence_vault_ids)
    found_ids = set(evidence_qs.values_list("vault_id", flat=True))
    missing = set(evidence_vault_ids) - found_ids
    if missing:
        raise ValueError(f"Evidence not found or access denied: {missing}")

    for ev in evidence_qs:
        if ev.reporter_id != reporter.id:
            raise ValueError(
                f"Evidence {ev.vault_id} does not belong to the reporting user. "
                "Only your own vault evidence can be referenced."
            )

    # Create report (no M2M yet so we have report.id for S3 paths)
    report = Report.objects.create(
        reporter=reporter,
        testimonial_text=(testimonial_text or "").strip(),
        digital_signature=digital_signature.strip(),
        signature_algorithm=(signature_algorithm or "RSA-SHA256").strip(),
        testimonial_voice_path="",
        testimonial_video_path="",
    )

    date_prefix = timezone.now().strftime("%Y/%m")
    base_path = f"report/testimonials/{date_prefix}"

    if testimonial_voice_file:
        ext = testimonial_voice_file.name.split(".")[-1] if "." in testimonial_voice_file.name else "bin"
        path = f"{base_path}/{report.id}_voice.{ext}"
        raw = testimonial_voice_file.read()
        saved = default_storage.save(path, ContentFile(raw))
        report.testimonial_voice_path = saved
        report.save(update_fields=["testimonial_voice_path"])

    if testimonial_video_file:
        ext = testimonial_video_file.name.split(".")[-1] if "." in testimonial_video_file.name else "bin"
        path = f"{base_path}/{report.id}_video.{ext}"
        raw = testimonial_video_file.read()
        saved = default_storage.save(path, ContentFile(raw))
        report.testimonial_video_path = saved
        report.save(update_fields=["testimonial_video_path"])

    report.evidences.set(evidence_qs)

    # Seal in blockchain
    block = ForensicLog.objects.create(
        event_type=ForensicLog.EventType.REPORT,
        evidence=None,
        report=report,
        evidence_hash_snapshot=_report_content_hash(report),
        actor_user_id=str(reporter.id),
        actor_role=reporter.role,
        notes=f"Report filed with {evidence_qs.count()} evidence item(s). "
        f"Testimonial: text={bool(report.testimonial_text)}, "
        f"voice={bool(report.testimonial_voice_path)}, video={bool(report.testimonial_video_path)}.",
    )

    return {
        "report_id": str(report.id),
        "block_number": block.block_number,
        "testimonial_voice_path": report.testimonial_voice_path or None,
        "testimonial_video_path": report.testimonial_video_path or None,
    }
