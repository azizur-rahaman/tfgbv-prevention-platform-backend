import hashlib
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    """
    Custom user model for Nirvhoy.
    Every account is tied to a Bangladesh National ID (NID) via a one-way SHA-256 hash.
    Raw NID numbers are NEVER stored — only the hash.
    """

    class UserRole(models.TextChoices):
        VICTIM = "victim", "Victim / Reporter"
        POLICE = "police", "Police Officer"
        FORENSIC_ANALYST = "forensic_analyst", "Forensic Analyst"
        BCC_ADMIN = "bcc_admin", "BCC / System Admin"
        JUDICIARY = "judiciary", "Judiciary / Magistrate"

    # --- Core Identity ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # SHA-256 hash of the raw NID number. Never store the real NID.
    nid_hash = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="SHA-256 hash of the National ID number. Raw NID is never stored.",
    )

    # Whether biometric verification via NIDW Partner API succeeded
    nid_verified = models.BooleanField(
        default=False,
        help_text="True only after successful biometric check via NIDW Partner API.",
    )

    # --- Role & Access ---
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VICTIM,
    )

    # For police officers — their official badge/ID number
    police_badge_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Official police badge ID. Only populated for police role.",
    )

    # Upazila assignment for police officers (Bangladesh has 495 upazilas)
    assigned_upazila = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="The upazila this officer is assigned to.",
    )

    # --- Contact ---
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Primary contact number (BD format: +880XXXXXXXXXX).",
    )

    # --- Audit ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # We use email as the primary contact, but username is still required by AbstractUser
    EMAIL_FIELD = "email"

    class Meta:
        verbose_name = "Nirvhoy User"
        verbose_name_plural = "Nirvhoy Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_role_display()} | {self.username}"

    # --- Helper Methods ---

    @staticmethod
    def hash_nid(raw_nid: str) -> str:
        """
        One-way SHA-256 hash of a raw NID string.
        Call this BEFORE saving. Never pass raw NID to the model directly.

        Usage:
            hashed = User.hash_nid("1234567890123")
            user.nid_hash = hashed
        """
        return hashlib.sha256(raw_nid.strip().encode("utf-8")).hexdigest()

    @property
    def is_police_officer(self) -> bool:
        return self.role == self.UserRole.POLICE

    @property
    def is_bcc_admin(self) -> bool:
        return self.role == self.UserRole.BCC_ADMIN

    @property
    def is_verified_victim(self) -> bool:
        """A victim whose NID has been confirmed via biometric check."""
        return self.role == self.UserRole.VICTIM and self.nid_verified


class AdminAuditLog(models.Model):
    """
    Audit log for BCC admin actions: user created, deactivated, role changed.
    Phase 1 model for BCC dashboard (Phase 5).
    """

    class ActionType(models.TextChoices):
        USER_CREATED = "user_created", "User Created"
        USER_DEACTIVATED = "user_deactivated", "User Deactivated"
        USER_ACTIVATED = "user_activated", "User Activated"
        ROLE_CHANGED = "role_changed", "Role Changed"

    actor_user_id = models.CharField(
        max_length=36,
        help_text="UUID of the BCC admin who performed the action.",
    )
    action = models.CharField(
        max_length=30,
        choices=ActionType.choices,
    )
    target_user_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="UUID of the user who was created/deactivated/edited.",
    )
    extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra context e.g. old_role, new_role.",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Audit Log"
        verbose_name_plural = "Admin Audit Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} by {self.actor_user_id} at {self.timestamp}"