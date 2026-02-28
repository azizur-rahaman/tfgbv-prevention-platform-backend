# Report API (Mobile)

The **report** app lets authenticated users file incident reports that reference evidence already in the vault, attach a testimonial (text, voice, or video), and a digital signature. Reports are stored in the DB, large files in the project S3 bucket, and each report is sealed in the blockchain.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/` | List current user's reports |
| POST | `/api/v1/reports/` | Create a new report (multipart) |
| GET | `/api/v1/reports/<report_id>/` | Get one report (owner only) |

**Authentication:** Bearer JWT (same as evidence API).

---

## POST /api/v1/reports/ — Place report

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_vault_ids` | string | Yes | JSON array of evidence vault UUIDs, e.g. `["uuid1", "uuid2"]`. Only evidence owned by the user can be referenced. |
| `testimonial_text` | string | No | Written testimonial (max 50000 chars). |
| `testimonial_voice` | file | No | Voice recording file (stored in S3). |
| `testimonial_video` | file | No | Video testimonial file (stored in S3). |
| `digital_signature` | string | Yes | Digital signature payload (e.g. base64 or hex from device). |
| `signature_algorithm` | string | No | Default `RSA-SHA256`. |

**Example (curl):**

```bash
curl -X POST "http://localhost:8000/api/v1/reports/" \
  -H "Authorization: Bearer <access_token>" \
  -F "evidence_vault_ids=[\"<vault-uuid-1>\", \"<vault-uuid-2>\"]" \
  -F "testimonial_text=Incident description..." \
  -F "digital_signature=<base64-or-hex-signature>" \
  -F "testimonial_voice=@/path/to/voice.m4a"
```

**Success (201):**

```json
{
  "success": true,
  "message": "Report filed and sealed in blockchain.",
  "report_id": "<uuid>",
  "block_number": 42,
  "testimonial_voice_stored": true,
  "testimonial_video_stored": false
}
```

**Errors:**

- `VALIDATION_ERROR`: invalid payload (e.g. malformed `evidence_vault_ids`, missing `digital_signature`).
- `REPORT_ERROR`: e.g. evidence not found or not owned by the user.

---

## GET /api/v1/reports/ — List reports

Returns all reports for the authenticated user.

**Success (200):**

```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "<uuid>",
      "created_at": "2026-02-28T12:00:00Z",
      "testimonial_text": "...",
      "has_voice": true,
      "has_video": false,
      "signature_algorithm": "RSA-SHA256",
      "evidence_count": 2
    }
  ]
}
```

---

## GET /api/v1/reports/<report_id>/ — Report detail

Returns a single report if it belongs to the current user. Includes `testimonial_voice_path` and `testimonial_video_path` (S3 paths); use presigned URLs or your own download flow for actual files.

**Success (200):**

```json
{
  "success": true,
  "report": {
    "id": "<uuid>",
    "reporter": "<user_id>",
    "created_at": "...",
    "updated_at": "...",
    "testimonial_text": "...",
    "testimonial_voice_path": "report/testimonials/2026/02/<id>_voice.m4a",
    "testimonial_video_path": "",
    "has_voice": true,
    "has_video": false,
    "signature_algorithm": "RSA-SHA256",
    "evidence_vault_ids": ["<vault_id_1>", "<vault_id_2>"]
  }
}
```

---

## Storage and blockchain

- **Voice/video:** Uploaded to the same S3 bucket as evidence, under `report/testimonials/YYYY/MM/<report_id>_voice.<ext>` and `_video.<ext>`.
- **Blockchain:** Each new report creates one `ForensicLog` block with `event_type=report`, linked to the report and a content hash, so the chain remains tamper-evident.
