# 02 — Architecture

## Directory Structure

```
src/
├── manage.py
├── db.sqlite3
├── .env                    # Not in repo; see dev_doc/setup.txt
├── core/                   # Django project package
│   ├── settings/
│   │   ├── __init__.py     # Imports local then base
│   │   ├── base.py         # Django + DRF + JWT + Crispy
│   │   └── local.py        # DB, MinIO, CORS, NID mock
│   ├── urls.py             # Root URLconf
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/           # User model, JWT auth API
│   ├── evidence/           # Evidence model, upload API, encryption
│   ├── blockchain/         # ForensicLog, chain verification
│   └── dashboard/          # Web UI (session auth)
├── templates/
│   ├── base.html
│   └── dashboard/          # Login, home, cases, chain, certificates, etc.
├── static/
└── media/                  # Overridden by S3 in local settings
```

## Applications

| App | Responsibility |
|-----|----------------|
| **accounts** | Custom user (NID hash, roles), JWT login/register/token refresh, admin. |
| **evidence** | Evidence CRUD, upload API, encryption/upload services, Section 65B–oriented metadata. |
| **blockchain** | Forensic log (hash chain), chain verification service, verify API. |
| **dashboard** | Session-based web UI for police/analysts: login, home, cases, case detail, chain verify, certificates. |

## URL Layout

**Root (`core/urls.py`):**

| Path | Target |
|------|--------|
| `admin/` | Django admin |
| `api/v1/auth/` | `apps.accounts.api.urls` |
| `api/v1/evidence/` | `apps.evidence.api.urls` |
| `api/v1/blockchain/` | `apps.blockchain.api.urls` |
| `""` | `apps.dashboard.urls` (dashboard at site root) |

**Dashboard URLs:** With `path("", include("apps.dashboard.urls"))`, dashboard is at **site root**: `/login/`, `/logout/`, `/`, `/cases/`, `/chain/`, `/certificates/`, etc. The effective base for dashboard is **`/dashboard/`** (from the project’s point of view; the exact prefix depends on how the root URLconf includes the app). Checking `core/urls.py`: `path("", include("apps.dashboard.urls"))` means dashboard is at **root**: `/login/`, `/cases/`, etc., not `/dashboard/login/`. So the dashboard is at **`/`** for login, home, cases, etc. **Note:** `LOGIN_URL` in base is `"/dashboard/login/"` — so either there is a top-level `path("dashboard/", include(...))` elsewhere or the login URL is configured for a different deployment. From the provided `core/urls.py` there is only `path("", include("apps.dashboard.urls"))`, so the actual login path is `/login/`. The settings `LOGIN_URL = "/dashboard/login/"` suggest the intention is to have dashboard under `/dashboard/`. This is a **configuration mismatch**: either add `path("dashboard/", include("apps.dashboard.urls"))` and change dashboard urls to be relative, or change `LOGIN_URL` to `/login/`. This is documented in **08-gaps-and-recommendations.md**.

**API v1:**

- **Auth:** `api/v1/auth/login/`, `api/v1/auth/register/`, `api/v1/auth/token/refresh/`
- **Evidence:** `api/v1/evidence/upload/`, `api/v1/evidence/<vault_id>/status/`
- **Blockchain:** `api/v1/blockchain/verify/`, `api/v1/blockchain/evidence/<vault_id>/`

## Data Flow (Evidence Upload)

1. **Flutter app** → POST multipart to `api/v1/evidence/upload/` (JWT).
2. **EvidenceUploadView** → Validates with `EvidenceUploadSerializer`, reads file bytes, calls `ingest_evidence()`.
3. **ingest_evidence()** (evidence.services.upload):
   - Verifies device hash vs raw bytes.
   - Encrypts (gzip + AES-256-GCM) via `encrypt_file()`.
   - Saves to default_storage (MinIO) at `evidence/YYYY/MM/<vault_id>.enc`.
   - Creates `Evidence` record.
   - Creates two `ForensicLog` entries: CAPTURE, VAULT_INGEST.
4. Response: vault_id, file_hash, block_number, status.

## Data Flow (Chain Verification)

- **Full chain:** `GET api/v1/blockchain/verify/` (police/forensic/bcc/judiciary) → `verify_chain_integrity()` → walks all `ForensicLog` by block_number, recomputes hash, checks previous_hash.
- **Single evidence:** `GET api/v1/blockchain/evidence/<vault_id>/` → `verify_single_evidence_chain(vault_id)` → same checks for blocks linked to that evidence.

## Dependencies (Imports)

No `requirements.txt` or `pyproject.toml` in repo. Inferred from code:

- django
- djangorestframework
- djangorestframework-simplejwt
- django-storages (S3/MinIO)
- django-crispy-forms, crispy-tailwind
- cryptography
- environ (django-environ)

Recommendation: add a `requirements.txt` (see **08-gaps-and-recommendations.md**).
