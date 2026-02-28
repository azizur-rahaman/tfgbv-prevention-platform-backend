# Postman Testing — Nirvhoy API

Use this folder to test the full API with Postman.

## Files

| File | Purpose |
|------|--------|
| `Nirvhoy_API_Collection.json` | Postman Collection: Auth, Evidence, Blockchain requests |
| `Nirvhoy_Environment.json` | Environment: `base_url`, `access_token`, `refresh_token`, `vault_id` |

## Import in Postman

1. Open Postman → **Import** → drag or select `Nirvhoy_API_Collection.json` and `Nirvhoy_Environment.json`.
2. Select the environment **Nirvhoy Local** (top-right).
3. Ensure your server is running:  
   `python manage.py runserver --settings=core.settings.local` (from `src/`).

## Recommended Test Order

### 1. Auth

- **Register (victim)** — creates `test_victim` / `testpass123`. Tokens are saved to the environment.
- **Login (victim)** — use the same credentials; tokens are saved again.
- **Token Refresh** — run after access_token expires; updates `access_token` in env.

For **Login (police)** and **Blockchain: Verify Chain**, create a dashboard user in Django admin (e.g. username `police_officer`, role **Police**), then log in with that user to get a token.

### 2. Evidence

- **Upload (multipart)**  
  - **Important:** `file_hash` must be the **SHA-256 hash of the file** you select, or the server returns `400 HASH_MISMATCH`.
  - **Option A:** Pick any small image (e.g. `test_data/sample.jpg`). Compute its hash:
    - **Windows (PowerShell):**  
      `Get-FileHash -Algorithm SHA256 .\sample.jpg | Select-Object -ExpandProperty Hash`
    - **Linux/Mac:**  
      `sha256sum sample.jpg`
    - Put the 64-character hex string into the `file_hash` field in the request.
  - **Option B:** Use the provided `test_data/sample_for_upload.txt` and set `file_hash` to  
    `9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08`  
    (SHA-256 of the word `test`).
  - On success, `vault_id` is stored in the environment.
- **Get Status** — uses `vault_id` from the environment (set by Upload or manually).

### 3. Blockchain

- **Verify Chain (full)** — requires a user with role **police**, **forensic_analyst**, **bcc_admin**, or **judiciary**. Log in as one of these, then run this request.
- **Get Evidence Chain** — uses `vault_id` from the environment.

## Environment Variables

| Variable | Set by | Use |
|----------|--------|-----|
| `base_url` | You (default: http://127.0.0.1:8000) | All request URLs |
| `access_token` | Login / Register / Token Refresh | `Authorization: Bearer {{access_token}}` |
| `refresh_token` | Login / Register | Token Refresh body |
| `vault_id` | Evidence Upload (test script) | Evidence Status, Evidence Chain |
| `user_id` | Login / Register | Optional reference |

## Sample Request Bodies (reference)

**Register (JSON):**
```json
{
    "username": "test_victim",
    "password": "testpass123",
    "phone_number": "+8801700000000",
    "nid_number": "1234567890123"
}
```

**Login (JSON):**
```json
{
    "username": "test_victim",
    "password": "testpass123"
}
```

**Token Refresh (JSON):**
```json
{
    "refresh": "<paste refresh_token here or use {{refresh_token}}>"
}
```

**Evidence Upload (form-data):**

| Key | Type | Value |
|-----|------|--------|
| file | File | Select file |
| file_hash | Text | SHA-256 of file (64 hex chars) |
| captured_at | Text | 2025-02-28T10:30:00+06:00 |
| evidence_type | Text | photo |
| harm_type | Text | harassment (or sextortion, image_abuse, doxxing, cyberbullying, other) |
| file_mime_type | Text | image/jpeg |
| description | Text | (optional) |
| assigned_upazila | Text | (optional) |

## Dashboard (browser)

- Login: http://127.0.0.1:8000/dashboard/login/
- Use a user with role Police, Forensic Analyst, BCC Admin, or Judiciary (create in Django admin).
