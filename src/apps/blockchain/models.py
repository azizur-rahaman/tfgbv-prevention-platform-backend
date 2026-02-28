import hashlib
from django.db import models
from django.utils import timezone


class ForensicLog(models.Model):
    """
    The internal blockchain ledger for Nirvhoy.

    Each entry contains a SHA-256 hash of its own data combined with
    the previous entry's hash. This creates a tamper-evident chain:
    if ANY record in the database is modified, every subsequent
    block_hash becomes invalid and the dashboard shows RED.

    This satisfies the 'unbroken chain of custody' requirement for
    Section 65B of the Bangladesh Evidence Act 2022.
    """

    class EventType(models.TextChoices):
        CAPTURE = "capture", "Initial Capture"
        VAULT_INGEST = "vault_ingest", "Vault Ingestion"
        ACCESS = "access", "Evidence Accessed"
        VERIFICATION = "verification", "Hash Verified"
        TRANSFER = "transfer", "Transferred to Court"
        VERDICT = "verdict", "Verdict Recorded"
        GENESIS = "genesis", "Genesis Block"

    # ------------------------------------------------------------------ #
    # CHAIN LINKS  (the blockchain structure)
    # ------------------------------------------------------------------ #
    previous_hash = models.CharField(
        max_length=64,
        help_text="Hash of the previous block. '000...0' for genesis.",
    )

    block_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="SHA-256 hash of this block's data + previous_hash.",
    )

    block_number = models.PositiveIntegerField(
        unique=True,
        help_text="Sequential block number. Genesis = 0.",
    )

    # ------------------------------------------------------------------ #
    # BLOCK DATA  (what this block is recording)
    # ------------------------------------------------------------------ #
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.CAPTURE,
    )

    # The evidence this block is about (null only for genesis block)
    evidence = models.ForeignKey(
        "evidence.Evidence",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="blockchain_logs",
        help_text="The evidence record this block is sealing.",
    )

    # The file hash at the time this block was created
    evidence_hash_snapshot = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Snapshot of Evidence.file_hash at the time of sealing.",
    )

    # Who triggered this event
    actor_user_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="UUID of the user who triggered this event.",
    )

    actor_role = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Role of the actor (victim, police, analyst).",
    )

    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Human-readable description of this event.",
    )

    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When this block was sealed.",
    )

    class Meta:
        verbose_name = "Forensic Log (Blockchain Block)"
        verbose_name_plural = "Forensic Log (Blockchain)"
        ordering = ["block_number"]

    def __str__(self):
        return f"Block #{self.block_number} | {self.get_event_type_display()} | {self.timestamp}"

    # ------------------------------------------------------------------ #
    # HASH COMPUTATION
    # ------------------------------------------------------------------ #
    def compute_hash(self) -> str:
        """
        Computes the SHA-256 hash for this block.
        Combines: event_type + evidence_hash + actor + timestamp + previous_hash

        IMPORTANT: timestamp must be cast to string BEFORE saving so the
        hash is deterministic. We use isoformat() for consistency.
        """
        content = (
            f"{self.block_number}"
            f"{self.event_type}"
            f"{self.evidence_hash_snapshot or ''}"
            f"{self.actor_user_id or ''}"
            f"{self.timestamp.isoformat()}"
            f"{self.previous_hash}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        """
        Auto-compute block_hash before saving.
        If this is a new block, auto-assign block_number and previous_hash.
        """
        if not self.pk:  # New block only
            # Get the last block in the chain
            last_block = ForensicLog.objects.order_by("-block_number").first()

            if last_block is None:
                # This is the genesis block
                self.block_number = 0
                self.previous_hash = "0" * 64
            else:
                self.block_number = last_block.block_number + 1
                self.previous_hash = last_block.block_hash

        # Always recompute the hash
        self.block_hash = self.compute_hash()
        super().save(*args, **kwargs)