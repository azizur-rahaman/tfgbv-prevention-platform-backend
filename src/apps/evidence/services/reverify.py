"""
Hash re-verification and encryption integrity for forensic analysts (Phase 4).
"""
import hashlib
from django.core.files.storage import default_storage

from apps.evidence.models import Evidence
from apps.evidence.services.encryption import decrypt_file


def reverify_evidence_hash(vault_id: str) -> dict:
    """
    Re-download from storage, decrypt, re-compute SHA-256, compare to stored file_hash.
    Returns report dict for forensic view.
    """
    try:
        evidence = Evidence.objects.get(vault_id=vault_id)
    except Evidence.DoesNotExist:
        return {"error": "Evidence not found", "match": False}

    if not evidence.storage_path:
        return {"error": "No storage path", "match": False}
    if not evidence.encryption_nonce:
        return {"error": "No encryption nonce", "match": False}

    try:
        with default_storage.open(evidence.storage_path, "rb") as f:
            encrypted_bytes = f.read()
    except Exception as e:
        return {"error": f"Storage read failed: {e}", "match": False}

    try:
        raw_bytes = decrypt_file(encrypted_bytes, bytes(evidence.encryption_nonce))
    except Exception as e:
        return {"error": f"Decrypt failed: {e}", "match": False}

    computed_hash = hashlib.sha256(raw_bytes).hexdigest()
    stored_hash = evidence.file_hash.lower()
    match = computed_hash == stored_hash

    return {
        "vault_id": str(vault_id),
        "match": match,
        "stored_hash": stored_hash,
        "computed_hash": computed_hash,
        "error": None if match else "Hash mismatch — possible tampering.",
        "bytes_verified": len(raw_bytes),
    }


def check_encryption_integrity(vault_id: str) -> dict:
    """
    Verify stored file size and nonce match Evidence record. Detects storage-layer tampering.
    """
    try:
        evidence = Evidence.objects.get(vault_id=vault_id)
    except Evidence.DoesNotExist:
        return {"error": "Evidence not found", "integrity_ok": False}

    if not evidence.storage_path:
        return {"error": "No storage path", "integrity_ok": False}

    try:
        with default_storage.open(evidence.storage_path, "rb") as f:
            encrypted_bytes = f.read()
    except Exception as e:
        return {"error": f"Storage read failed: {e}", "integrity_ok": False}

    actual_size = len(encrypted_bytes)
    stored_size = evidence.stored_size_bytes or 0
    size_ok = actual_size == stored_size
    nonce_ok = evidence.encryption_nonce is not None and len(evidence.encryption_nonce) == 12

    return {
        "vault_id": str(vault_id),
        "integrity_ok": size_ok and nonce_ok,
        "stored_size_recorded": stored_size,
        "actual_size_in_storage": actual_size,
        "size_match": size_ok,
        "nonce_present": nonce_ok,
        "error": None if (size_ok and nonce_ok) else (
            f"Size mismatch: record={stored_size}, storage={actual_size}" if not size_ok else "Nonce missing or invalid"
        ),
    }
