# 05 — Services

Business logic lives in service modules; API views and dashboard views call into them.

---

## evidence.services.encryption

**Path:** `src/apps/evidence/services/encryption.py`

- **get_master_key() -> bytes**  
  Reads `EVIDENCE_ENCRYPTION_KEY` from settings (32-byte key from hex). Raises if not 32 bytes.

- **encrypt_file(raw_bytes: bytes) -> tuple[bytes, bytes]**  
  1. Gzip compress (level 9).  
  2. 12-byte random nonce.  
  3. AES-256-GCM encrypt.  
  Returns `(encrypted_bytes, nonce)`.

- **decrypt_file(encrypted_bytes, nonce) -> bytes**  
  Decrypt then gzip decompress; returns raw bytes (re-hashing should match Evidence.file_hash).

---

## evidence.services.upload

**Path:** `src/apps/evidence/services/upload.py`

- **_verify_hash(raw_bytes: bytes, submitted_hash: str) -> bool**  
  SHA-256(raw_bytes) compared to submitted_hash (lowercased). Used to reject tampered uploads.

- **ingest_evidence(...) -> dict**  
  Main pipeline called by EvidenceUploadView.  
  **Steps:**  
  1. **Hash check** — _verify_hash(raw_file, submitted_hash); on failure raises ValueError (HASH_MISMATCH).  
  2. **Encrypt** — encrypt_file(raw_file) → encrypted_bytes, nonce.  
  3. **Build Evidence** (unsaved) with vault_id, reporter, file_hash, captured_at, type, harm, mime, geo, description, device, app_version, sizes, is_encrypted=True, is_compressed=True, encryption_nonce=nonce, is_hash_verified=True, status=VERIFIED.  
  4. **Storage path** — `evidence/YYYY/MM/<vault_id>.enc`.  
  5. **Save file** — default_storage.save(path, ContentFile(encrypted_bytes)); set evidence.storage_path to saved_path.  
  6. **Save Evidence.**  
  7. **ForensicLog** — two blocks: CAPTURE (notes: type, harm, device), VAULT_INGEST (notes: saved_path).  
  **Returns:** vault_id, status, file_hash, stored_path, block_number (from last block for this evidence).

**Parameters:** reporter, raw_file, submitted_hash, captured_at, evidence_type, harm_type, file_mime_type; optional latitude, longitude, description, device_id, app_version.

---

## blockchain.services

**Path:** `src/apps/blockchain/services.py`

- **verify_chain_integrity() -> dict**  
  Loads all ForensicLog ordered by block_number. For each block: recompute hash, check previous_hash equals expected (genesis: "0"*64), check block_hash equals recomputed. Builds list of block_status dicts. On first failure returns immediately with is_intact=False, broken_at_block, error, blocks_checked.  
  **Returns:** is_intact, total_blocks, broken_at_block, error, blocks_checked.

- **verify_single_evidence_chain(vault_id: str) -> dict**  
  Filters ForensicLog by evidence__vault_id=vault_id, ordered by block_number. For each block: recompute hash, compare to stored block_hash.  
  **Returns:** is_intact (all valid), error (None or message), blocks (list of block_number, event_type display, timestamp, is_valid, notes).

---

## Integration

- **Evidence upload** → ingest_evidence creates Evidence and two ForensicLog entries; API returns block_number.  
- **Evidence status** → API returns blockchain_entries from ForensicLog for that evidence.  
- **Dashboard** — home and chain view use verify_chain_integrity(); case detail and certificate use verify_single_evidence_chain(vault_id).
