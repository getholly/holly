from __future__ import annotations

from typing import Any

import requests
from django.conf import settings
from loguru import logger


class CaddyManagerService:
    """Service for managing Caddy reverse proxy."""

    def __init__(self) -> None:
        self.caddy_api_url: str = settings.CADDY_API_URL
        self.domain_suffix: str = settings.CADDY_DOMAIN_SUFFIX

    def register_service(self, subdomain: str, ip: str, port: int) -> bool:
        """Create DNS and Caddy mapping for the given container."""
        domain = f"{subdomain}.{self.domain_suffix}"
        if not self.create_dns_record(domain, ip):
            logger.error("Failed to create DNS record for %s", domain)
            return False
        if not self._update_caddy(domain, ip, port):
            logger.error("Failed to update Caddy for %s", domain)
            return False
        return True

    def create_dns_record(self, domain: str, ip: str) -> bool:
        """Create a DNS record for the domain pointing to the IP address."""
        try:
            # Placeholder for DNS provider integration
            logger.info("Creating DNS record %s -> %s", domain, ip)
            # TODO: Integrate with DNS provider
            return True
        except Exception as exc:  # pragma: no cover - external integration
            logger.error("Unable to create DNS record: %s", exc)
            return False

    def _update_caddy(self, domain: str, ip: str, port: int) -> bool:
        """Update Caddy configuration to route requests."""
        try:
            config = self._get_config()
            server = (
                config.setdefault("apps", {})
                .setdefault("http", {})
                .setdefault("servers", {})
                .setdefault("dynamic", {"listen": [":80"], "routes": []})
            )
            server["routes"].append(
                {
                    "match": [{"host": [domain]}],
                    "handle": [
                        {
                            "handler": "reverse_proxy",
                            "upstreams": [{"dial": f"{ip}:{port}"}],
                        }
                    ],
                }
            )
            resp = requests.post(f"{self.caddy_api_url}/load", json=config, timeout=5)
            resp.raise_for_status()
            return True
        except Exception as exc:  # pragma: no cover - external integration
            logger.error("Failed to update Caddy config: %s", exc)
            return False

    def _get_config(self) -> dict[str, Any]:
        try:
            resp = requests.get(f"{self.caddy_api_url}/config/", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # pragma: no cover - external integration
            logger.warning("Failed to fetch Caddy config: %s", exc)
            return {}
