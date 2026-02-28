import os
from pathlib import Path
import environ

# ------------------------------------------------------------------ #
# BASE_DIR points to the project root (where manage.py lives)
# Path: core/settings/base.py  →  .parent = settings/
#                                 .parent.parent = core/
#                                 .parent.parent.parent = src/ (root)
# ------------------------------------------------------------------ #
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ------------------------------------------------------------------ #
# Load .env IMMEDIATELY here in base.py so every setting below can
# safely call env(). This is the fix for the SECRET_KEY empty error.
# ------------------------------------------------------------------ #
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ------------------------------------------------------------------ #
# CORE DJANGO SETTINGS
# ------------------------------------------------------------------ #
SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ------------------------------------------------------------------ #
# APPLICATIONS
# ------------------------------------------------------------------ #
INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Nirvhoy apps
    "apps.accounts",
    "apps.evidence",
    "apps.blockchain",
    "apps.report",
    "apps.dashboard",
    # Third-party
    "storages",
    "rest_framework",
    "rest_framework_simplejwt",
    "crispy_forms",
    "crispy_tailwind",
]

# ------------------------------------------------------------------ #
# MIDDLEWARE
# ------------------------------------------------------------------ #
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ------------------------------------------------------------------ #
# URL / WSGI
# ------------------------------------------------------------------ #
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ------------------------------------------------------------------ #
# TEMPLATES  (required for Django admin to work)
# ------------------------------------------------------------------ #
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ------------------------------------------------------------------ #
# CUSTOM AUTH USER MODEL
# ------------------------------------------------------------------ #
AUTH_USER_MODEL = "accounts.User"

# ------------------------------------------------------------------ #
# PASSWORD VALIDATION
# ------------------------------------------------------------------ #
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------ #
# INTERNATIONALISATION
# ------------------------------------------------------------------ #
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"   # Bangladesh Standard Time (UTC+6)
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------ #
# STATIC & MEDIA
# ------------------------------------------------------------------ #
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------ #
# DEFAULT PRIMARY KEY
# ------------------------------------------------------------------ #
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Evidence encryption key (AES-256-GCM master key)
EVIDENCE_ENCRYPTION_KEY = env("EVIDENCE_ENCRYPTION_KEY")

# ------------------------------------------------------------------ #
# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------ #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

APPEND_SLASH = False

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Dashboard login redirect
LOGIN_URL = "/dashboard/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/dashboard/login/"