# ruff: noqa: E501
from loguru import logger

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env
from .email import *  # noqa: F403 Import email settings

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env("DJANGO_DEBUG", default=False)

# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="!!!SET DJANGO_SECRET_KEY!!!",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["getholly.ai", "www.getholly.ai"]

CSRF_TRUSTED_ORIGINS = ["https://getholly.ai", "https://www.getholly.ai", "https://static.getholly.ai"]


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
STATIC_URL = f"{AWS_S3_CUSTOM_DOMAIN}/static/"  # Or appropriate path
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

# endregion

# region admin
ADMIN_SITE_HEADER = "Holly AI Prod"
ADMIN_SITE_TITLE = "Holly AI Prod"
ADMIN_INDEX_TITLE = "Welcome to Holly AI Dashboard"

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

CORS_ALLOWED_ORIGINS = ["https://getholly.ai", "https://www.getholly.ai", "https://static.getholly.ai"]
CORS_ALLOWED_ORIGIN_REGEXES = [r"https://.*\.getholly\.ai$"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_SHARED_WORKER = True
# endregion

# Frontend URL for production
FRONTEND_URL = env.str("FRONTEND_URL", default="https://getholly.ai")

# GitHub App webhook configuration for production
GITHUB_WEBHOOK_SECRET = env.str("GITHUB_WEBHOOK_SECRET", default="")

SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SECURE_SSL_REDIRECT = not DEBUG  # Force HTTPS
SECURE_HSTS_SECONDS = 31536000  # HTTP Strict Transport Security
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
