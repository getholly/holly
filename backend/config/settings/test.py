# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="cP2UvfsXvwvA2kT0yv0qe8Hlo41madxCnUYgjLZOfgkR2VWKKJ53SwRM9AnA6RQX",
)


# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"


# Disable any caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

DEBUG = False  # disable for faster testing


# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Include anymail in INSTALLED_APPS for testing, but use locmem backend
if "anymail" not in INSTALLED_APPS:
    INSTALLED_APPS += ["anymail"]

# Set up dummy Anymail settings for tests
ANYMAIL = {
    "POSTMARK_SERVER_TOKEN": "test_server_token",
    "POSTMARK_API_URL": "https://api.postmarkapp.com/",
    "POSTMARK_TRACK_OPENS": False,
    "POSTMARK_TRACK_CLICKS": False,
}
