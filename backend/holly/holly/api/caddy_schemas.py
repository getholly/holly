from ninja import Schema


class CaddyMapRequest(Schema):
    """Request schema for mapping a container through Caddy."""

    subdomain: str
    ip: str
    port: int


class CaddyMapResponse(Schema):
    """Response schema for Caddy mapping operations."""

    success: bool
    domain: str
    message: str
