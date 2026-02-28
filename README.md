# Nirvhoy (TFGBV Prevention Platform) — Backend

Nirvhoy is a Django backend for a **technology-facilitated gender-based violence (TFGBV)** prevention platform. It supports:

- **Mobile app users (victims/reporters)**: register/login, upload digital evidence (photo/video/audio/document), and file incident reports.
- **Institutional users**: **Police**, **Forensic Analysts**, **BCC Admins**, and **Judiciary** use a role-specific **web dashboard** for case handling, chain-of-custody verification, and legal documentation.
- **Legal compliance**: evidence handling is designed around **Bangladesh Evidence Act 2022 — Section 65B** (electronic evidence admissibility and chain-of-custody).

All application code lives under `src/`.

---

## Documentation in this repository

- **Audit (how the codebase works)**: `audit/`  
  Start with `audit/01-overview.md` and `audit/02-architecture.md`.
- **Dashboard implementation plan/spec**: `implementation/`
- **Developer docs**: `dev_doc/` (includes `dev_doc/report_api.md` and `dev_doc/create_dashboard_accounts.md`)
- **Postman collection/environment**: `postman/`

---

## Core features (what the system does)

### Evidence vault (mobile → backend → storage)

1. Mobile app uploads a file (multipart) and provides its **SHA-256** hash.
2. Backend recomputes SHA-256 to detect tampering in transit.
3. Backend **compresses (gzip)** and **encrypts (AES-256-GCM)** the bytes.
4. Encrypted bytes are stored in **S3-compatible storage** (MinIO in development) under a `.enc` object key.
5. An `Evidence` record is created in the database and sealed in a tamper-evident chain (`ForensicLog`).

### Tamper-evident ledger (“blockchain”)

The `apps.blockchain.ForensicLog` model implements a **permissioned chained ledger** (not a public cryptocurrency blockchain). Each block links to the previous via hashes; verification detects any modification.

Key event types include:

- `GENESIS`, `CAPTURE`, `VAULT_INGEST`
- `TRANSFER` (submission/forwarding)
- `VERDICT` (judiciary disposition)
- `REPORT` (report filed and sealed)

### Reports (mobile API → police confirmation → court flow)

The `apps.report` app lets a user file a report that:

- references one or more existing evidence `vault_id` values,
- includes a testimonial (text, optional voice/video),
- includes a digital signature payload,
- stores large testimonial media in S3/MinIO,
- creates a `ForensicLog` block (`event_type=REPORT`) to seal the report.

Workflow:

- **New reports** start as `pending_police`.
- **Police** can review report details in the dashboard and **approve/forward to court** (judiciary).
- When forwarded, linked evidence is marked `submitted` (so it appears in judiciary lists).

### Role-specific dashboards (server-rendered)

Dashboard users authenticate via Django session login and are redirected to role-specific home pages.

- **Police**: case inbox, report confirmation and detail views, chain verification, 65B certificates, mark evidence for court submission.
- **Forensic Analyst**: flagged queue, chain audit, tamper log, hash re-verification, encryption integrity checks, expert report PDF.
- **Judiciary**: submitted cases only, chain verification, 65B certificates, record court disposition.
- **BCC Admin**: system oversight views (some admin templates exist; scope may vary by phase).

### Encrypted evidence preview (dashboard)

On the case detail page, the dashboard can display the encrypted evidence file **after server-side decryption**, based on file type:

- image: rendered inline
- video/audio: playable via browser controls
- other types: download link

This is served from a dashboard route that enforces the same role-based access as the case detail view.

---

## Project structure (high level)

```
audit/                 # Codebase audit docs
implementation/        # Dashboard plan/spec docs
dev_doc/               # Developer notes and API docs
postman/               # Postman collection + environment
src/
  apps/
    accounts/          # Custom User + JWT auth (API)
    evidence/          # Evidence model + ingest/encryption services + API
    blockchain/        # ForensicLog ledger + verification services + API
    report/            # Report model + submission services + API
    dashboard/         # Role dashboards (views, permissions, templates)
  core/                # Django project settings + urls
  templates/           # Dashboard templates
```

---

## API overview (mobile clients)

Base paths (see `audit/04-apis.md` and `dev_doc/report_api.md` for details):

- **Auth**: `/api/v1/auth/` (JWT)
- **Evidence**: `/api/v1/evidence/`
- **Reports**: `/api/v1/reports/`
- **Blockchain**: `/api/v1/blockchain/`

Important evidence rule:

- Evidence upload is rejected unless the provided `file_hash` equals the SHA-256 of the uploaded file bytes (`HASH_MISMATCH`).

---

## Dashboard overview (browser)

Dashboard is mounted at:

- **Login**: `/dashboard/login/`
- **Home** (redirects by role): `/dashboard/`

Common routes (availability depends on role):

- Cases: `/dashboard/cases/`, case detail: `/dashboard/cases/<vault_id>/`
- Chain verify: `/dashboard/chain/`
- Certificates: `/dashboard/certificates/`
- Police reports: `/dashboard/police/reports/`

Account creation guide:

- `dev_doc/create_dashboard_accounts.md`

---

## Configuration (environment variables)

Settings are split under `src/core/settings/`. Environment variables are loaded using `django-environ` from `src/.env`.

Common variables:

- **Django**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- **Crypto**: `EVIDENCE_ENCRYPTION_KEY` (required, 32 bytes as 64 hex chars)
- **Database**: `DATABASE_URL` (defaults to sqlite)
- **Storage (S3/MinIO)**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME`
- **NID partner (dev/mock)**: `NIDW_API_KEY`, `NIDW_PARTNER_ID`

Generating an AES-256 key (example):

```bash
python -c "import os,binascii; print(binascii.hexlify(os.urandom(32)).decode())"
```

---

## Local development (quick start)

### Prerequisites

- Python 3.10+ (project uses modern Django/DRF patterns)
- An S3-compatible service for storage (MinIO recommended for local development)

### Install dependencies

This repository currently does **not** include a `requirements.txt`/`pyproject.toml`. Install the primary dependencies (minimum set) in your virtual environment:

- `django`
- `djangorestframework`
- `djangorestframework-simplejwt`
- `django-environ`
- `django-storages`
- `boto3`
- `cryptography`
- `django-crispy-forms`
- `crispy-tailwind`
- `reportlab` (PDF generation)

### Run the server

From the repository root:

```bash
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open:

- Dashboard: `/dashboard/login/`
- Admin: `/admin/`

---

## Testing

### Postman

Import the Postman files in `postman/` and follow:

- `postman/README.md`

### Report API

See:

- `dev_doc/report_api.md`

---

## Security notes (development vs production)

- Evidence files are **encrypted at rest** in storage; decryption occurs server-side for authorized dashboard users.
- The current dashboard evidence preview endpoint returns decrypted bytes as an **inline** response; for large media, consider adding **streaming/range requests** and stricter auditing in production.
- Do not commit `.env` files or real credentials. Rotate `SECRET_KEY` and storage keys for any deployed environment.

---

## Where to look next

- **Understand architecture**: `audit/02-architecture.md`
- **Models**: `audit/03-models.md`
- **APIs**: `audit/04-apis.md`
- **Dashboard**: `audit/06-dashboard.md`
- **Configuration**: `audit/07-config-and-deployment.md`
- **Gaps/recommendations**: `audit/08-gaps-and-recommendations.md`

