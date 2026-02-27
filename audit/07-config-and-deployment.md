# 07 — Config and Deployment

## Settings layout

- **Entry:** `core.settings` (DJANGO_SETTINGS_MODULE).  
- **core/settings/__init__.py** imports: `from .local import *` then `from .base import *` (so local overrides base).
- **base.py** — Django core, DRF, JWT, Crispy, static/media, AUTH_USER_MODEL, EVIDENCE_ENCRYPTION_KEY.  
- **local.py** — Imports base; overrides: DATABASES, AWS_* (MinIO), NIDW_*, CORS, DEBUG.

## Environment variables

Loaded in **base.py** via `environ` from `src/.env` (path: BASE_DIR / ".env").  
**BASE_DIR** = project root where manage.py lives (src/).

| Variable | Used in | Purpose |
|----------|---------|---------|
| SECRET_KEY | base | Django secret |
| DEBUG | base (default False) | Overridden True in local |
| ALLOWED_HOSTS | base (list) | e.g. localhost, 127.0.0.1 |
| EVIDENCE_ENCRYPTION_KEY | base | 32-byte hex key for AES-256-GCM |
| DATABASE_URL | local | default sqlite:///db.sqlite3 |
| AWS_ACCESS_KEY_ID | local | MinIO |
| AWS_SECRET_ACCESS_KEY | local | MinIO |
| AWS_STORAGE_BUCKET_NAME | local | e.g. nirvhoy-vault |
| AWS_S3_ENDPOINT_URL | local | e.g. http://localhost:9000 |
| AWS_S3_REGION_NAME | local | default us-east-1 |
| NIDW_API_KEY | local | NID mock (default mock_nid_key_for_demo) |
| NIDW_PARTNER_ID | local | NID mock (default nirvhoy_dev_01) |

## Key settings (base)

- **AUTH_USER_MODEL** = "accounts.User"
- **APPEND_SLASH** = False
- **DRF:** JWTAuthentication; IsAuthenticated; JSONRenderer
- **Simple JWT:** access 12h, refresh 7d, HS256, Bearer
- **Crispy:** tailwind template pack
- **LOGIN_URL** = "/dashboard/login/"  
- **LOGIN_REDIRECT_URL** = "/dashboard/"  
- **LOGOUT_REDIRECT_URL** = "/dashboard/login/"  

With current URLconf (dashboard at root), `/dashboard/` and `/dashboard/login/` do not exist unless you add a `dashboard/` prefix in root urls. See **08-gaps**.

## Local overrides (local.py)

- **DATABASES:** from env.db("DATABASE_URL", default="sqlite:///db.sqlite3").
- **STORAGES:** default = S3Boto3Storage (MinIO); staticfiles = StaticFilesStorage.  
  S3 options: path-style, no overwrite, querystring auth for presigned.
- **CORS_ALLOW_ALL_ORIGINS** = True.
- **DEBUG** = True.

## Running the app

- Set **DJANGO_SETTINGS_MODULE** to `core.settings` (or `core.settings.local` if you use a separate local entry).  
- From **src/:** `python manage.py runserver` (and migrate, createsuperuser as needed).  
- MinIO: create bucket (e.g. nirvhoy-vault); see dev_doc/setup.txt for Docker and .env.  
- **Genesis block:** Create once after migrations (see dev_doc/setup.txt): ForensicLog with event_type=GENESIS; block_number/previous_hash/block_hash set in model save().

## Dependencies

No requirements.txt in repo. See **02-architecture.md** and **08-gaps-and-recommendations.md** for inferred list and recommendation to add one.
