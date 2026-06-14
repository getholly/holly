"""Optional bearer-token authentication for the in-container REST API.

The container REST API exposes git/file/conversation operations that act with the
mission's GitHub credentials, so it must not be open to anyone who can reach the
port. Authentication is enforced whenever ``REST_MCP_API_TOKEN`` is set in the
container environment; callers must then present ``Authorization: Bearer <token>``.

It is left opt-in (no token configured => no enforcement) so existing deployments
keep working until every Django caller is wired to send the header. Provision
``REST_MCP_API_TOKEN`` on the container and send it from all callers to enable.
"""

import hmac
import os

from fastapi import Header, HTTPException, status

_API_TOKEN = os.getenv("REST_MCP_API_TOKEN")


async def require_api_token(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency enforcing the bearer token when one is configured."""
    if not _API_TOKEN:
        # No token configured: enforcement disabled (backward compatible).
        return

    expected = f"Bearer {_API_TOKEN}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
