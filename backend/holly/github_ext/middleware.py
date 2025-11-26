import logging

from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from requests_oauthlib import OAuth2Session


# https://codeberg.org/allauth/django-allauth/issues/420
def oauth_session_enforcement(get_response):
    """
    For any user authenticated via GitHub OAuth, ensure their token has not expired.
    If expired, attempt to refresh it. If refresh fails, log them out.
    """

    github_provider = settings.SOCIALACCOUNT_PROVIDERS.get("github", {})
    logger = logging.getLogger(f"{__name__}.{oauth_session_enforcement.__name__}")

    def middleware(request):
        if not hasattr(request, "user"):
            error_string = (
                "oauth_session_enforcement must be included in middlewares after "
                "django.contrib.auth.middleware.AuthenticationMiddleware or equivalent"
            )
            raise ImproperlyConfigured(error_string)

        user = request.user
        try:
            social_token = SocialToken.objects.get(account__user_id=user.id)
        except SocialToken.DoesNotExist:
            # User is not authenticated via GitHub OAuth, allow request
            social_token = None

        if social_token is None:
            return get_response(request)

        # Check if the token is still valid
        if social_token.expires_at and social_token.expires_at > timezone.now():
            return get_response(request)

        adapter = GitHubOAuth2Adapter(request)

        try:
            logger.debug("Refreshing access token for %s", user)

            oauth_session = OAuth2Session(
                client_id=github_provider["APP"]["client_id"],
                token={
                    "access_token": social_token.token,
                    "refresh_token": social_token.token_secret,
                    "token_type": "Bearer",
                },
            )

            new_token_data = oauth_session.refresh_token(
                token_url=adapter.access_token_url,
                client_id=github_provider["APP"]["client_id"],
                client_secret=github_provider["APP"]["secret"],
            )

            new_social_token = adapter.parse_token(new_token_data)

            # Replace the existing token instead of creating a new one
            new_social_token.id = social_token.id
            new_social_token.app_id = social_token.app_id
            new_social_token.account_id = social_token.account_id
            new_social_token.save()

        except Exception:
            logger.exception("Failed to refresh expired access token")
            logout(request)

        return get_response(request)

    return middleware
