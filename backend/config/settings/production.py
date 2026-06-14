# ruff: noqa: E501
from loguru import logger

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, NINJA_JWT, SALT_KEY, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env("DJANGO_DEBUG", default=False)

# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="!!!SET DJANGO_SECRET_KEY!!!",
)

# Fail fast if security-critical secrets were left at their insecure defaults.
# These feed JWT signing and field-level encryption; a known/default value means
# forgeable tokens and decryptable secrets.
_INSECURE_SECRET_DEFAULTS = {"!!!SET DJANGO_SECRET_KEY!!!", "dummy_secret_auth_key"}
if SECRET_KEY in _INSECURE_SECRET_DEFAULTS:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set to a strong, unique value in production.")
if SALT_KEY == ["f2fa786c-021c-4103-acdf-82cea504eaae"]:
    raise ImproperlyConfigured("SALT_KEY must be set to a unique value in production (field encryption salt).")

# NINJA_JWT is defined in base.py and binds SIGNING_KEY to base.py's SECRET_KEY at
# import time. Re-point it at the production SECRET_KEY resolved above so tokens are
# signed with the real secret rather than base's default fallback.
NINJA_JWT["SIGNING_KEY"] = SECRET_KEY
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["getholly.ai", "www.getholly.ai"]

CSRF_TRUSTED_ORIGINS = ["https://getholly.ai", "https://www.getholly.ai", "https://static.getholly.ai"]


# DATABASE
# ------------------------------------------------------------------------------
# Prefer a real database (e.g. Postgres) via DATABASE_URL so web and Celery
# workers share one database. SQLite (the base default) is single-writer and,
# when only the web service mounts the file, leaves workers on a separate DB.
DATABASE_URL = env.str("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    logger.warning(
        "DATABASE_URL not set in production; falling back to SQLite. Set DATABASE_URL "
        "(e.g. postgres://...) so web and Celery workers share one database."
    )


# CACHES
# ------------------------------------------------------------------------------
# Use Redis (shared across worker processes) when REDIS_URL is configured;
# LocMemCache is per-process and useless for cross-worker state / throttling.
REDIS_CACHE_URL = env.str("REDIS_CACHE_URL", default="")
if REDIS_CACHE_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_CACHE_URL}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "",
        },
    }


# Email
# ------------------------------------------------------------------------------
# Use Anymail with Postmark in production
EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"

# Get Postmark server token from environment
POSTMARK_SERVER_TOKEN = env("POSTMARK_SERVER_TOKEN", default="")
if not POSTMARK_SERVER_TOKEN:
    logger.warning("POSTMARK_SERVER_TOKEN not set. Email functionality will not work correctly.")

# Update Anymail with Postmark settings
ANYMAIL = {
    "POSTMARK_SERVER_TOKEN": POSTMARK_SERVER_TOKEN,
    "POSTMARK_INBOUND_SECRET": env("POSTMARK_INBOUND_SECRET", default=""),
}

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# Your stuff...
# ------------------------------------------------------------------------------


TEST_CHAT_RESPONSES = env.bool("TEST_CHAT_RESPONSES", False)

# region S3
# Cloudflare R2 settings
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
    },
}

# R2 credentials
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", "your_access_key")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", "your_secret_key")
AWS_STORAGE_BUCKET_NAME = "llmrepo"
AWS_S3_ENDPOINT_URL = "https://bc2043c616d427139c181d21fc6274c7.r2.cloudflarestorage.com"
AWS_S3_CUSTOM_DOMAIN = "static.getholly.ai"  # If using a custom domain

# R2-specific settings
AWS_S3_REGION_NAME = "auto"  # R2 doesn't need a specific region
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = "public-read"

# Static files configuration
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"  # Or appropriate path
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

# endregion

# region admin
ADMIN_SITE_HEADER = "Holly AI Prod"
ADMIN_SITE_TITLE = "Holly AI Prod"
ADMIN_INDEX_TITLE = "Welcome to Holly AI Dashboard"

# endregion

# region security
# These are deliberately unconditional (not gated on DEBUG) so a stray
# DJANGO_DEBUG=True in production cannot silently disable HTTPS enforcement.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True  # Force HTTPS
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply to subdomains
SECURE_HSTS_PRELOAD = True  # Allow your site to be included in HSTS preload lists

DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB (adjust as needed)
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB (adjust as needed)

CORS_ALLOWED_ORIGINS = ["https://getholly.ai", "https://www.getholly.ai", "https://static.getholly.ai"]
# Single-label subdomains only (avoid matching dots so attacker-controlled
# multi-level hosts like evil.attacker.getholly.ai are not trusted with credentials).
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://[a-z0-9-]+\.getholly\.ai$"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_SHARED_WORKER = True
# endregion

# Frontend URL for production
FRONTEND_URL = env.str("FRONTEND_URL", default="https://getholly.ai")

# GitHub App webhook configuration for production
GITHUB_WEBHOOK_SECRET = env.str("GITHUB_WEBHOOK_SECRET", default="")
