import hashlib
import gzip
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.evidence.models import Evidence
from apps.blockchain.models import ForensicLog
from apps.evidence.services.encryption import encrypt_file


def _verify_hash(raw_bytes: bytes, submitted_hash: str) -> bool:
    """
    Re-computes SHA-256 of the raw bytes and compares to
    the hash submitted by the Flutter app.
    Returns True only if they match exactly.
    """
    server_hash = hashlib.sha256(raw_bytes).hexdigest()
    return server_hash == submitted_hash.lower()


def ingest_evidence(
    reporter,
    raw_file: bytes,
    submitted_hash: str,
    captured_at,
    evidence_type: str,
    harm_type: str,
    file_mime_type: str,
    latitude=None,
    longitude=None,
    description=None,
    device_id=None,
    app_version=None,
) -> dict:
    """
    The main forensic ingest pipeline. Called by the API view.

    Steps:
        1. Verify submitted hash matches raw file bytes
        2. Encrypt + compress the file
        3. Upload encrypted bytes to MinIO
        4. Create Evidence record in database
        5. Seal in ForensicLog (blockchain)

    Returns a dict with vault_id and status.
    Raises ValueError if hash verification fails.
    """

    # ------------------------------------------------------------------ #
    # STEP 1 — Hash Verification
    # This is the most critical step. If hash doesn't match,
    # the file was tampered with in transit. Reject immediately.
    # ------------------------------------------------------------------ #
    if not _verify_hash(raw_file, submitted_hash):
        raise ValueError(
            "HASH_MISMATCH: Submitted hash does not match file contents. "
            "Evidence rejected — possible tampering in transit."
        )

    original_size = len(raw_file)

    # ------------------------------------------------------------------ #
    # STEP 2 — Encrypt + Compress
    # ------------------------------------------------------------------ #
    encrypted_bytes, nonce = encrypt_file(raw_file)
    stored_size = len(encrypted_bytes)

    # ------------------------------------------------------------------ #
    # STEP 3 — Upload to MinIO (BCC Cloud Simulation)
    # File is stored encrypted. Path: evidence/YYYY/MM/vault_id.enc
    # ------------------------------------------------------------------ #
    # We create the Evidence instance first to get the vault_id (UUID)
    evidence = Evidence(
        reporter=reporter,
        file_hash=submitted_hash.lower(),
        captured_at=captured_at,
        evidence_type=evidence_type,
        harm_type=harm_type,
        file_mime_type=file_mime_type,
        latitude=latitude,
        longitude=longitude,
        description=description,
        device_id=device_id,
        app_version=app_version,
        original_size_bytes=original_size,
        stored_size_bytes=stored_size,
        is_encrypted=True,
        is_compressed=True,
        encryption_nonce=nonce,
        is_hash_verified=True,   # We just verified above
        status=Evidence.EvidenceStatus.VERIFIED,
    )

    # Build storage path using vault_id
    date_prefix = timezone.now().strftime("%Y/%m")
    storage_path = f"evidence/{date_prefix}/{evidence.vault_id}.enc"

    # Upload to MinIO via django-storages
    saved_path = default_storage.save(
        storage_path,
        ContentFile(encrypted_bytes)
    )
    evidence.storage_path = saved_path

    # Save the Evidence record
    evidence.save()

    # ------------------------------------------------------------------ #
    # STEP 4 — Seal in Blockchain (ForensicLog)
    # ------------------------------------------------------------------ #
    ForensicLog.objects.create(
        event_type=ForensicLog.EventType.CAPTURE,
        evidence=evidence,
        evidence_hash_snapshot=evidence.file_hash,
        actor_user_id=str(reporter.id),
        actor_role=reporter.role,
        notes=(
            f"Evidence captured via Nirvhoy mobile app. "
            f"Type: {evidence_type}. Harm: {harm_type}. "
            f"Device: {device_id or 'unknown'}."
        ),
    )

    ForensicLog.objects.create(
        event_type=ForensicLog.EventType.VAULT_INGEST,
        evidence=evidence,
        evidence_hash_snapshot=evidence.file_hash,
        actor_user_id=str(reporter.id),
        actor_role=reporter.role,
        notes=f"Encrypted file stored at: {saved_path}",
    )

    return {
        "vault_id": str(evidence.vault_id),
        "status": evidence.status,
        "file_hash": evidence.file_hash,
        "stored_path": saved_path,
        "block_number": ForensicLog.objects.filter(
            evidence=evidence
        ).last().block_number,
    }