from __future__ import annotations

import ipaddress
import re
from typing import Any

import requests
from django.conf import settings
from loguru import logger

# Subdomain labels per RFC 1035 (and to prevent host-header/route injection).
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


class CaddyManagerService:
    """Service for managing Caddy reverse proxy."""

    def __init__(self) -> None:
        self.caddy_api_url: str = settings.CADDY_API_URL
        self.domain_suffix: str = settings.CADDY_DOMAIN_SUFFIX
        self.allowed_network = ipaddress.ip_network(settings.CADDY_ALLOWED_UPSTREAM_NETWORK)

    def _validate_target(self, subdomain: str, ip: str, port: int) -> bool:
        """Reject anything that could turn /caddy/map into an SSRF / open proxy."""
        if not _SUBDOMAIN_RE.match(subdomain):
            logger.error(f"Rejected invalid Caddy subdomain: {subdomain!r}")
            return False
        if not (1 <= port <= 65535):
            logger.error(f"Rejected out-of-range Caddy port: {port}")
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            logger.error(f"Rejected invalid Caddy upstream IP: {ip!r}")
            return False
        if addr not in self.allowed_network:
            logger.error(f"Rejected Caddy upstream IP outside container network: {ip}")
            return False
        return True

    def register_service(self, subdomain: str, ip: str, port: int) -> bool:
        """Create DNS and Caddy mapping for the given container."""
        if not self._validate_target(subdomain, ip, port):
            return False
        domain = f"{subdomain}.{self.domain_suffix}"
        if not self.create_dns_record(domain, ip):
            logger.error(f"Failed to create DNS record for {domain}")
            return False
        if not self._update_caddy(domain, ip, port):
            logger.error(f"Failed to update Caddy for {domain}")
            return False
        return True

    def create_dns_record(self, domain: str, ip: str) -> bool:
        """Create a DNS record for the domain pointing to the IP address."""
        try:
            # Placeholder for DNS provider integration
            logger.info(f"Creating DNS record {domain} -> {ip}")
            # TODO: Integrate with DNS provider
            return True
        except Exception as exc:  # pragma: no cover - external integration
            logger.error(f"Unable to create DNS record: {exc}")
            return False

    def _update_caddy(self, domain: str, ip: str, port: int) -> bool:
        """Update Caddy configuration to route requests."""
        config = self._get_config()
        if config is None:
            # Don't rebuild a fresh config from scratch on a fetch failure — that
            # would POST a near-empty config to /load and wipe all existing routes.
            logger.error("Aborting Caddy update: could not read current config")
            return False
        try:
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
            logger.error(f"Failed to update Caddy config: {exc}")
            return False

    def _get_config(self) -> dict[str, Any] | None:
        """Return the current Caddy config, or None if it cannot be read."""
        try:
            resp = requests.get(f"{self.caddy_api_url}/config/", timeout=5)
            resp.raise_for_status()
            return resp.json() or {}
        except Exception as exc:  # pragma: no cover - external integration
            logger.warning(f"Failed to fetch Caddy config: {exc}")
            return None
