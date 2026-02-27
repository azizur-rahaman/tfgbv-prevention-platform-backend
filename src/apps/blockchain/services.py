import hashlib
from apps.blockchain.models import ForensicLog


def verify_chain_integrity() -> dict:
    """
    Walks every block in the ForensicLog from genesis to latest.
    Recomputes each block_hash and checks the previous_hash linkage.

    Returns:
        {
            "is_intact": True/False,
            "total_blocks": int,
            "broken_at_block": int or None,
            "error": str or None,
            "blocks_checked": list
        }
    """
    logs = ForensicLog.objects.order_by("block_number")

    if not logs.exists():
        return {
            "is_intact": False,
            "total_blocks": 0,
            "broken_at_block": None,
            "error": "No blocks found. Genesis block missing.",
            "blocks_checked": [],
        }

    blocks_checked = []
    expected_previous_hash = "0" * 64  # Genesis block's previous_hash

    for block in logs:
        # Recompute what the hash SHOULD be
        recomputed_hash = block.compute_hash()

        block_status = {
            "block_number": block.block_number,
            "event_type": block.event_type,
            "timestamp": block.timestamp.isoformat(),
            "stored_hash": block.block_hash,
            "recomputed_hash": recomputed_hash,
            "previous_hash_ok": block.previous_hash == expected_previous_hash,
            "hash_ok": block.block_hash == recomputed_hash,
            "is_valid": (
                block.previous_hash == expected_previous_hash
                and block.block_hash == recomputed_hash
            ),
        }
        blocks_checked.append(block_status)

        # If either check fails — chain is broken
        if not block_status["previous_hash_ok"]:
            return {
                "is_intact": False,
                "total_blocks": logs.count(),
                "broken_at_block": block.block_number,
                "error": (
                    f"Block #{block.block_number} has wrong previous_hash. "
                    f"Expected: {expected_previous_hash[:16]}... "
                    f"Got: {block.previous_hash[:16]}..."
                ),
                "blocks_checked": blocks_checked,
            }

        if not block_status["hash_ok"]:
            return {
                "is_intact": False,
                "total_blocks": logs.count(),
                "broken_at_block": block.block_number,
                "error": (
                    f"Block #{block.block_number} hash mismatch. "
                    f"Data was tampered. "
                    f"Stored: {block.block_hash[:16]}... "
                    f"Recomputed: {recomputed_hash[:16]}..."
                ),
                "blocks_checked": blocks_checked,
            }

        # Move to next expected link
        expected_previous_hash = block.block_hash

    return {
        "is_intact": True,
        "total_blocks": logs.count(),
        "broken_at_block": None,
        "error": None,
        "blocks_checked": blocks_checked,
    }


def verify_single_evidence_chain(vault_id: str) -> dict:
    """
    Verifies the chain integrity for a specific evidence item only.
    Used by the police dashboard when opening a single case.
    """
    logs = ForensicLog.objects.filter(
        evidence__vault_id=vault_id
    ).order_by("block_number")

    if not logs.exists():
        return {
            "is_intact": False,
            "error": f"No blockchain entries found for vault_id: {vault_id}",
            "blocks": [],
        }

    blocks = []
    for block in logs:
        recomputed = block.compute_hash()
        is_valid = block.block_hash == recomputed
        blocks.append({
            "block_number": block.block_number,
            "event_type": block.get_event_type_display(),
            "timestamp": block.timestamp.isoformat(),
            "is_valid": is_valid,
            "notes": block.notes,
        })

    all_valid = all(b["is_valid"] for b in blocks)

    return {
        "is_intact": all_valid,
        "error": None if all_valid else "Hash mismatch detected in evidence chain.",
        "blocks": blocks,
    }