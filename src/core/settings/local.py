# ------------------------------------------------------------------ #
# LOCAL / HACKATHON SETTINGS
# .env is already loaded in base.py — do NOT load it again here.
# This file only overrides settings that differ from base.py.
# ------------------------------------------------------------------ #
from .base import *  # noqa: F401, F403  — imports everything from base

# ------------------------------------------------------------------ #
# DATABASE  —  SQLite for portability (entire DB is one file)
# ------------------------------------------------------------------ #
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")
}

# ------------------------------------------------------------------ #
# MINIO / BCC CLOUD STORAGE SIMULATION
# Uses django-storages + boto3 to talk to your local MinIO container.
# ------------------------------------------------------------------ #
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")

# Required for MinIO (it doesn't use AWS signature v4 query auth)
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "path"        # MinIO needs path-style, not virtual-hosted
AWS_DEFAULT_ACL = None                  # Don't set public ACL on uploads
AWS_S3_FILE_OVERWRITE = False           # Never overwrite evidence files
AWS_QUERYSTRING_AUTH = True             # Presigned URLs require auth params

# Django 4.2+ uses STORAGES dict instead of DEFAULT_FILE_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ------------------------------------------------------------------ #
# NID MOCK CREDENTIALS (for prototype demo)
# ------------------------------------------------------------------ #
NIDW_API_KEY = env("NIDW_API_KEY", default="mock_nid_key_for_demo")
NIDW_PARTNER_ID = env("NIDW_PARTNER_ID", default="nirvhoy_dev_01")

# ------------------------------------------------------------------ #
# DEVELOPMENT RELAXATIONS
# ------------------------------------------------------------------ #
CORS_ALLOW_ALL_ORIGINS = True           # Allow Flutter app on any port

# Show full error pages in browser during development
DEBUG = True