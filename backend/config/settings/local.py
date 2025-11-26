# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="!!!SET DJANGO_SECRET_KEY!!!",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "0.0.0.0", "127.0.0.1", "host.docker.internal"])  # noqa: S104

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
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# Use console backend for local development unless POSTMARK_SERVER_TOKEN is set
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# Postmark configuration for local development (if token provided)
POSTMARK_SERVER_TOKEN = env("POSTMARK_SERVER_TOKEN", default="")
ANYMAIL={}
if POSTMARK_SERVER_TOKEN:
    EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"
    ANYMAIL["POSTMARK_SERVER_TOKEN"] = POSTMARK_SERVER_TOKEN

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]

# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Disable profiling panel due to an issue with Python 3.12:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]


# Your stuff...
# ------------------------------------------------------------------------------


TEST_CHAT_RESPONSES = env.bool("TEST_CHAT_RESPONSES", True)

# Base URL for containers to call back into this Django instance (Windows Docker Desktop)
# Containers will send webhooks to f"{DJANGO_BASE_URL}/_api/holly/webhooks/container-webhook"
DJANGO_BASE_URL = env.str("DJANGO_BASE_URL", default="http://host.docker.internal:8000")

# CORS settings for development with Vite
CSRF_TRUSTED_ORIGINS = []
CORS_ALLOWED_ORIGINS = []
for port in (5173, 5174, 5175, 3000):
    CSRF_TRUSTED_ORIGINS += [f"http://localhost:{port}", f"http://127.0.0.1:{port}"]
    CORS_ALLOWED_ORIGINS += [f"http://localhost:{port}", f"http://127.0.0.1:{port}"]

CORS_ALLOW_CREDENTIALS = True  # Allow cookies to be sent with requests
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]  # Expose these headers to JS
