from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja.security import APIKeyHeader
from ninja.security.http import HttpBearer, logger as http_logger
from ninja_jwt.authentication import JWTAuth

User = get_user_model()


class ApiKeyAuth(APIKeyHeader):
    """API key authentication for Django Ninja."""

    param_name = "X-API-Key"

    def authenticate(self, request: HttpRequest, key: str) -> Any | None:
        """Authenticate a request using an API key.

        In a production scenario, you would validate this against a database.
        This is a simple placeholder implementation.
        """
        try:
            # Replace this with actual API key validation logic
            # For simplicity, we're just checking against settings here
            # In production, you would verify the key against a secured database entry
            if settings.DEBUG and key == getattr(settings, "API_KEY", "test_api_key"):
                # Return the user or any value that represents the authenticated entity
                return True
            return None
        except Exception:
            return None


class AsyncJWTAuth(JWTAuth):
    is_async = True

    async def __call__(self, request: HttpRequest) -> Any | None:  # type: ignore[override]
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None

        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            if settings.DEBUG:
                http_logger.error(f"Unexpected auth - '{auth_value}'")
            return None

        token = " ".join(parts[1:])

        user = await sync_to_async(self.jwt_authenticate, thread_sensitive=True)(request, token)
        request.user = user
        return user
