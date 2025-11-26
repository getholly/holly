from django.http import HttpRequest
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.caddy_schemas import CaddyMapRequest, CaddyMapResponse
from holly.holly.services.caddy_manager import CaddyManagerService

router = Router(auth=JWTAuth())
service = CaddyManagerService()


@router.post("/map", response=CaddyMapResponse)
def map_container(request: HttpRequest, data: CaddyMapRequest) -> CaddyMapResponse:
    """Map a container port via Caddy."""
    success = service.register_service(data.subdomain, data.ip, data.port)
    domain = f"{data.subdomain}.{service.domain_suffix}"
    message = "Mapping created" if success else "Failed to create mapping"
    return CaddyMapResponse(success=success, domain=domain, message=message)
