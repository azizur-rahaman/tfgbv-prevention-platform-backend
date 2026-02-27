# 04 — APIs

All API routes are under **`/api/v1/`**. Auth for mobile: **JWT Bearer**.  
DRF default: `IsAuthenticated`; auth endpoints use `AllowAny`.

---

## Auth — `api/v1/auth/`

**Base URL:** `api/v1/auth/`  
**Module:** `apps.accounts.api.views`  
**URLs:** `apps.accounts.api.urls`

### POST `login/`

- **View:** `MobileLoginView`
- **Permission:** AllowAny
- **Body (JSON):** `username`, `password`
- **Success (200):**  
  `{ "success": true, "access": "<jwt>", "refresh": "<refresh>", "user": { "id", "username", "role", "nid_verified" } }`
- **Errors:** 400 missing credentials; 401 invalid credentials.

### POST `register/`

- **View:** `MobileRegisterView`
- **Permission:** AllowAny
- **Body (JSON):** `username`, `password`, `phone_number` (optional), `nid_number` (raw NID — hashed server-side)
- **Success (201):**  
  `{ "success": true, "message": "...", "access", "refresh", "user": { "id", "username", "role" } }`
- **Errors:** 400 validation / username exists / NID already registered.

### POST `token/refresh/`

- **View:** DRF `TokenRefreshView` (Simple JWT)
- **Body:** `refresh`: refresh token
- **Returns:** New access token (and optionally refresh) per Simple JWT config.

---

## Evidence — `api/v1/evidence/`

**Base URL:** `api/v1/evidence/`  
**Module:** `apps.evidence.api.views`  
**URLs:** `apps.evidence.api.urls`  
**Auth:** JWT required (except where noted).

### POST `upload/`

- **View:** `EvidenceUploadView`
- **Parsers:** MultiPartParser, FormParser
- **Body (multipart/form-data):**  
  `file`, `file_hash` (64-char hex), `captured_at` (ISO 8601), `evidence_type`, `harm_type`, `file_mime_type`, optional: `latitude`, `longitude`, `description`, `device_id`, `app_version`
- **Success (201):**  
  `{ "success": true, "message": "...", "vault_id", "file_hash", "block_number", "status" }`
- **Errors:** 400 validation (VALIDATION_ERROR + details) or HASH_MISMATCH; 500 SERVER_ERROR.

### GET `<vault_id>/status/`

- **View:** `EvidenceStatusView`
- **Path:** `api/v1/evidence/<uuid:vault_id>/status/`
- **Behaviour:** Reporter-only (filter by `reporter=request.user`).
- **Success (200):**  
  `{ "success": true, "vault_id", "status", "is_hash_verified", "uploaded_at", "blockchain_entries": [ { "block_number", "event_type", "timestamp", "notes" }, ... ] }`
- **Errors:** 404 NOT_FOUND if not found or not reporter’s.

---

## Blockchain — `api/v1/blockchain/`

**Base URL:** `api/v1/blockchain/`  
**Module:** `apps.blockchain.api.views`  
**URLs:** `apps.blockchain.api.urls`  
**Auth:** JWT required.

### GET `verify/`

- **View:** `ChainIntegrityView`
- **Roles:** POLICE, FORENSIC_ANALYST, BCC_ADMIN, JUDICIARY only.
- **Success (200):**  
  `{ "success": true, "chain_status": "INTACT"|"COMPROMISED", "is_intact", "total_blocks", "broken_at_block", "error", "blocks_checked" }`
- **Errors:** 403 if role not allowed.

### GET `evidence/<vault_id>/`

- **View:** `EvidenceChainView`
- **Path:** `api/v1/blockchain/evidence/<uuid:vault_id>/`
- **Success (200):**  
  `{ "success": true, "vault_id", "chain_status", "is_intact", "error", "blocks" }`
- **Access:** Authenticated; no extra role check in view (any JWT can query any vault_id chain).

---

## Serializers

- **Evidence upload:** `EvidenceUploadSerializer` in `apps.evidence.api.serializers` — validates file, file_hash (64 hex), captured_at, evidence_type, harm_type, file_mime_type, optional geo/description/device/app_version; `validate_file_hash` ensures hex.
