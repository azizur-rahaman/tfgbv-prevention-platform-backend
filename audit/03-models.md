# 03 — Models

## accounts.User

**Path:** `src/apps/accounts/models.py`  
**Base:** `AbstractUser` (Django)  
**Purpose:** Custom user for Nirvhoy; every account tied to a Bangladesh NID via SHA-256 hash (raw NID never stored).

| Field | Type | Notes |
|-------|------|--------|
| id | UUIDField (PK) | default=uuid.uuid4, editable=False |
| nid_hash | CharField(64) | unique, null, blank — SHA-256 of raw NID |
| nid_verified | BooleanField | default False — set after NIDW Partner API biometric check |
| role | CharField(20) | UserRole choices, default VICTIM |
| police_badge_id | CharField(50) | null, blank — for police role |
| assigned_upazila | CharField(100) | null, blank — for police (495 upazilas in BD) |
| phone_number | CharField(15) | null, blank — BD format +880... |
| created_at | DateTimeField | auto_now_add=True |
| updated_at | DateTimeField | auto_now=True |

**UserRole choices:** VICTIM, POLICE, FORENSIC_ANALYST, BCC_ADMIN, JUDICIARY.

**Methods / helpers:**
- `User.hash_nid(raw_nid: str) -> str` — static; SHA-256 of raw NID (use before saving).
- `is_police_officer`, `is_bcc_admin`, `is_verified_victim` — properties.

**Meta:** verbose_name "Nirvhoy User", ordering `["-created_at"]`.

---

## evidence.Evidence

**Path:** `src/apps/evidence/models.py`  
**Purpose:** Core forensic record; file reference, hash, metadata for Section 65B admissibility.

| Field | Type | Notes |
|-------|------|--------|
| vault_id | UUIDField (PK) | default uuid.uuid4, editable=False — stable reference in storage/API |
| reporter | FK(accounts.User) | on_delete=PROTECT, related_name="evidence_reports" |
| file_hash | CharField(64) | SHA-256 from device at capture |
| storage_path | CharField(500) | Path in BCC/MinIO e.g. evidence/2025/01/uuid.enc |
| file_size_bytes | PositiveBigIntegerField | null, blank |
| file_mime_type | CharField(100) | null, blank |
| is_encrypted | BooleanField | default True (AES-256-GCM) |
| encryption_nonce | BinaryField(max 12) | null, blank — per-file nonce |
| is_compressed | BooleanField | default True (gzip) |
| original_size_bytes | PositiveBigIntegerField | null, blank — before compress/encrypt |
| stored_size_bytes | PositiveBigIntegerField | null, blank — after |
| latitude, longitude | DecimalField(9,6) | null, blank — GPS at capture |
| captured_at | DateTimeField | Device network time at capture |
| uploaded_at | DateTimeField | auto_now_add — server ingest time |
| evidence_type | CharField(20) | EvidenceType choices, default PHOTO |
| harm_type | CharField(20) | HarmType choices, default OTHER |
| description | TextField | null, blank |
| status | CharField(20) | EvidenceStatus choices, default PENDING |
| is_hash_verified | BooleanField | default False — server re-hash confirmed |
| verified_by | FK(User) | null, blank, SET_NULL, related_name="verified_evidence" |
| verified_at | DateTimeField | null, blank |
| device_id | CharField(200) | null, blank — anonymised device id |
| app_version | CharField(20) | null, blank |

**EvidenceType:** PHOTO, VIDEO, AUDIO, SCREENSHOT, DOCUMENT.  
**EvidenceStatus:** PENDING, VERIFIED, FLAGGED, SUBMITTED.  
**HarmType:** SEXTORTION, IMAGE_ABUSE, DOXXING, CYBERBULLYING, HARASSMENT, OTHER.

**Indexes:** (reporter, status), file_hash, uploaded_at.

**Methods:** `verify_hash() -> bool` — currently returns `is_hash_verified` (placeholder for production re-hash from storage).

---

## blockchain.ForensicLog

**Path:** `src/apps/blockchain/models.py`  
**Purpose:** Tamper-evident hash chain (internal “blockchain”) for chain of custody; Section 65B.

| Field | Type | Notes |
|-------|------|--------|
| previous_hash | CharField(64) | Hash of previous block; "0"*64 for genesis |
| block_hash | CharField(64) | unique — SHA-256 of this block data + previous_hash |
| block_number | PositiveIntegerField | unique — sequential; genesis = 0 |
| event_type | CharField(20) | EventType choices, default CAPTURE |
| evidence | FK(evidence.Evidence) | null, blank, PROTECT, related_name="blockchain_logs" |
| evidence_hash_snapshot | CharField(64) | null, blank — Evidence.file_hash at seal time |
| actor_user_id | CharField(100) | null, blank |
| actor_role | CharField(50) | null, blank |
| notes | TextField | null, blank |
| timestamp | DateTimeField | default timezone.now |

**EventType:** CAPTURE, VAULT_INGEST, ACCESS, VERIFICATION, TRANSFER, GENESIS.

**Methods:**
- `compute_hash() -> str` — SHA-256(block_number, event_type, evidence_hash_snapshot, actor_user_id, timestamp.isoformat(), previous_hash).
- `save()` — New block: assigns block_number and previous_hash from last block; genesis uses block_number=0, previous_hash="0"*64. Always sets block_hash = compute_hash() before save.

**Meta:** ordering `["block_number"]`.

---

## dashboard

**Path:** `src/apps/dashboard/models.py`  
**Content:** Empty (no models); dashboard uses Evidence and ForensicLog from other apps.
