# ruff: noqa: E501
from loguru import logger

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, NINJA_JWT, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env("DJANGO_DEBUG", default=False)

# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="!!!SET DJANGO_SECRET_KEY!!!",
)
# Re-point the JWT signing key at this environment's SECRET_KEY (NINJA_JWT is
# built in base.py against base's SECRET_KEY at import time).
NINJA_JWT["SIGNING_KEY"] = SECRET_KEY
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["app-develop.getholly.ai", ".getholly.ai", "host.docker.internal"])

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS",
                                default=["https://develop.getholly.ai", "https://app-develop.getholly.ai",
                                         "https://app-getholly.ai", "https://static.getholly.ai",
                                 "https://*.getholly.ai"])

# DATABASE
# ------------------------------------------------------------------------------
# Share one database across web and Celery workers when DATABASE_URL is set.
DATABASE_URL = env.str("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES = {"default": env.db("DATABASE_URL")}

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
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

# Base URL for containers to call back into this Django instance (Windows Docker Desktop)
# Containers will send webhooks to f"{DJANGO_BASE_URL}/_api/holly/webhooks/container-webhook"
DJANGO_BASE_URL = env.str("DJANGO_BASE_URL", default="http://host.docker.internal:8000")

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
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", "llmrepo-dev")
AWS_S3_ENDPOINT_URL = "https://bc2043c616d427139c181d21fc6274c7.r2.cloudflarestorage.com"
AWS_S3_CUSTOM_DOMAIN = "static-develop.getholly.ai"  # If using a custom domain

# R2-specific settings
AWS_S3_REGION_NAME = "auto"  # R2 doesn't need a specific region
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = "public-read"

# Static files configuration
STATIC_URL = f"{AWS_S3_CUSTOM_DOMAIN}/static/"  # Or appropriate path
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

# endregion

# region admin
ADMIN_SITE_HEADER = "Holly Develop"
ADMIN_SITE_TITLE = "Holly Develop"
ADMIN_INDEX_TITLE = "Welcome to Holly Dashboard(Develop)"

# endregion

# region security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply to subdomains
SECURE_HSTS_PRELOAD = True  # Allow your site to be included in HSTS preload lists

DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB (adjust as needed)
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB (adjust as needed)

CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ALLOWED_ORIGINS",
                                default=["https://develop.getholly.ai", "https://static-develop.getholly.ai", ])
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://[a-z0-9-]+\.getholly\.ai$"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_SHARED_WORKER = True
# endregion
