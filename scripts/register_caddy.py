#!/usr/bin/env python
"""Register subdomain routing with a running Caddy instance."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


def get_persistence_file() -> Path:
    """Get the path to the persistence file for storing registered routes."""
    persistence_dir = Path(os.environ.get("CADDY_PERSISTENCE_DIR", "/tmp/caddy-routes"))
    persistence_dir.mkdir(exist_ok=True)
    return persistence_dir / "registered_routes.json"


def load_persisted_routes() -> dict[str, dict[str, Any]]:
    """Load previously registered routes from persistence file."""
    persistence_file = get_persistence_file()
    if not persistence_file.exists():
        return {}
    
    try:
        with open(persistence_file, 'r') as f:
            routes = json.load(f)
        logger.debug("Loaded %d persisted routes", len(routes))
        return routes
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load persisted routes: %s", e)
        return {}


def save_persisted_routes(routes: dict[str, dict[str, Any]]) -> None:
    """Save registered routes to persistence file."""
    persistence_file = get_persistence_file()
    try:
        with open(persistence_file, 'w') as f:
            json.dump(routes, f, indent=2)
        logger.debug("Saved %d routes to persistence file", len(routes))
    except OSError as e:
        logger.error("Failed to save persisted routes: %s", e)


def save_caddy_config_backup(caddy_host: str) -> None:
    """Save current Caddy configuration as backup."""
    config = check_caddy_config(caddy_host)
    if not config:
        logger.warning("Could not get Caddy config for backup")
        return
    
    backup_file = get_persistence_file().parent / "caddy_config_backup.json"
    try:
        with open(backup_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.debug("Saved Caddy config backup")
    except OSError as e:
        logger.error("Failed to save Caddy config backup: %s", e)


def restore_routes_from_persistence(caddy_host: str) -> None:
    """Restore all persisted routes to Caddy."""
    routes = load_persisted_routes()
    if not routes:
        logger.info("No persisted routes to restore")
        return
    
    logger.info("Restoring %d persisted routes", len(routes))
    for subdomain, route_info in routes.items():
        try:
            port = route_info["port"]
            register_subdomain(subdomain, port, caddy_host, persist=False, configure_auto_https=True)
            logger.info("Restored route for %s", subdomain)
        except Exception as e:
            logger.error("Failed to restore route for %s: %s", subdomain, e)


def check_caddy_config(caddy_host: str) -> Dict[str, Any] | None:
    """Check current Caddy configuration and return it."""
    try:
        config_url = f"http://{caddy_host}/config/"
        logger.debug("Checking Caddy config at %s", config_url)
        response = requests.get(config_url, timeout=5)
        response.raise_for_status()
        config = response.json()
        logger.debug("Current Caddy config: %s", config)
        return config
    except Exception as e:
        logger.error("Failed to get Caddy config: %s", e)
        return None


def get_server_name(caddy_host: str) -> str:
    """Get the first available server name from Caddy config, or default."""
    config = check_caddy_config(caddy_host)
    if (
        config
        and "apps" in config
        and "http" in config["apps"]
        and "servers" in config["apps"]["http"]
    ):
        servers = config["apps"]["http"]["servers"]
        if servers:
            server_name = list(servers.keys())[0]
            logger.debug("Found server name: %s", server_name)
            return server_name

    logger.warning("No servers found in config, using default 'srv0'")
    return "srv0"


def extract_container_name(subdomain: str) -> str:
    """Extract container name from subdomain (e.g., '9751e8b.github.me.uk' -> 'pr-9751e8b')."""
    # Extract the prefix before the first dot
    container_name = subdomain.split('.')[0]
    logger.debug("Extracted container name '%s' from subdomain '%s'", container_name, subdomain)
    return container_name


def ensure_auto_https_config(caddy_host: str, server_name: str) -> None:
    """Ensure auto_https disable_redirects is configured for the server."""
    try:
        # Check current server config
        server_url = f"http://{caddy_host}/config/apps/http/servers/{server_name}"
        response = requests.get(server_url, timeout=5)
        response.raise_for_status()
        server_config = response.json()
        
        # Check if auto_https is already configured correctly
        current_auto_https = server_config.get("automatic_https", {})
        if current_auto_https.get("disable_redirects") is True:
            logger.debug("auto_https disable_redirects already configured")
            return
        
        # Update the auto_https configuration
        auto_https_config = {
            "disable_redirects": True
        }
        
        # Merge with existing automatic_https config if it exists
        if current_auto_https:
            auto_https_config.update(current_auto_https)
            auto_https_config["disable_redirects"] = True
        
        auto_https_url = f"http://{caddy_host}/config/apps/http/servers/{server_name}/automatic_https"
        logger.debug("Setting auto_https config at %s: %s", auto_https_url, auto_https_config)
        
        response = requests.patch(auto_https_url, json=auto_https_config, timeout=10)
        response.raise_for_status()
        logger.info("Configured auto_https disable_redirects for server %s", server_name)
        
    except requests.exceptions.RequestException as e:
        logger.warning("Failed to configure auto_https settings: %s", e)
        # Don't fail the registration if auto_https config fails
    except Exception as e:
        logger.warning("Unexpected error configuring auto_https: %s", e)


def register_subdomain(subdomain: str, port: int, caddy_host: str, persist: bool = True, configure_auto_https: bool = True) -> None:
    """Register ``subdomain`` to proxy to ``port`` using the Caddy API."""
    # Get the actual server name from the current config
    server_name = get_server_name(caddy_host)
    
    # Ensure auto_https disable_redirects is configured (unless disabled)
    if configure_auto_https:
        ensure_auto_https_config(caddy_host, server_name)
    
    # Extract container name from subdomain
    container_name = extract_container_name(subdomain)
    target_address = f"{container_name}:{port}"
    
    logger.info("Registering subdomain '%s' to proxy to container '%s'", subdomain, target_address)

    route_config: Dict[str, Any] = {
        "@id": subdomain,
        "match": [{"host": [subdomain]}],
        "handle": [
            {
                "handler": "reverse_proxy",
                "upstreams": [{"dial": target_address}],
            }
        ],
    }

    # First, get current routes and remove any existing routes for this subdomain
    try:
        current_config = check_caddy_config(caddy_host)
        if (
            current_config
            and "apps" in current_config
            and "http" in current_config["apps"]
            and "servers" in current_config["apps"]["http"]
            and server_name in current_config["apps"]["http"]["servers"]
        ):
            current_routes = current_config["apps"]["http"]["servers"][server_name].get(
                "routes", []
            )
            logger.debug("Current routes count: %d", len(current_routes))

            # Remove any existing routes for this subdomain
            filtered_routes = []
            removed_count = 0
            for route in current_routes:
                # Check if this route matches our subdomain
                if isinstance(route.get("match"), list):
                    should_remove = False
                    for match in route["match"]:
                        if (
                            isinstance(match.get("host"), list)
                            and subdomain in match["host"]
                        ):
                            should_remove = True
                            break
                    if should_remove:
                        removed_count += 1
                        logger.debug(
                            "Removing existing route for subdomain: %s", subdomain
                        )
                        continue

                # Check for @id match as well
                if route.get("@id") == subdomain:
                    removed_count += 1
                    logger.debug("Removing existing route with @id: %s", subdomain)
                    continue

                filtered_routes.append(route)

            if removed_count > 0:
                logger.info(
                    "Removed %d existing route(s) for subdomain: %s",
                    removed_count,
                    subdomain,
                )

            # Add our new route to the beginning of the filtered routes array
            new_routes = [route_config] + filtered_routes

            # Replace the entire routes array
            url = f"http://{caddy_host}/config/apps/http/servers/{server_name}/routes"
            logger.debug(f"Updating routes at {url} with {new_routes}")

            response = requests.patch(url, json=new_routes, timeout=10)
            response.raise_for_status()
            logger.info("Registered %s to proxy to container %s", subdomain, target_address)
            
            # Persist the route information if requested
            if persist:
                routes = load_persisted_routes()
                routes[subdomain] = {
                    "port": port,
                    "container_name": container_name,
                    "target_address": target_address,
                    "registered_at": __import__("datetime").datetime.now().isoformat()
                }
                save_persisted_routes(routes)
                # Also save a backup of the current Caddy config
                save_caddy_config_backup(caddy_host)
        else:
            logger.error("Could not find server %s in Caddy config", server_name)
            raise RuntimeError(f"Server {server_name} not found in Caddy configuration")

    except requests.exceptions.HTTPError as e:
        logger.error("Caddy API HTTP error: %s", e)
        if "response" in locals():
            logger.error("Response status code: %s", response.status_code)
            logger.error("Response headers: %s", dict(response.headers))
            logger.error("Response body: %s", response.text)

        # Try to get current Caddy config for debugging
        check_caddy_config(caddy_host)

        raise
    except requests.exceptions.RequestException as e:
        logger.error("Caddy API request error: %s", e)
        logger.error("Failed to connect to Caddy API")
        raise


def unregister_subdomain(subdomain: str, caddy_host: str, persist: bool = True) -> None:
    """Remove previously registered ``subdomain`` from Caddy."""
    url = f"http://{caddy_host}/id/{subdomain}"
    logger.debug("Deleting config via %s", url)

    try:
        response = requests.delete(url, timeout=10)
        response.raise_for_status()
        logger.info("Unregistered %s", subdomain)
        
        # Remove from persistence if requested
        if persist:
            routes = load_persisted_routes()
            if subdomain in routes:
                del routes[subdomain]
                save_persisted_routes(routes)
                logger.debug("Removed %s from persisted routes", subdomain)
    except requests.exceptions.HTTPError as e:
        logger.error("Caddy API HTTP error during unregister: %s", e)
        logger.error("Response status code: %s", response.status_code)
        logger.error("Response headers: %s", dict(response.headers))
        logger.error("Response body: %s", response.text)

        # If it's a 404, the subdomain wasn't registered, which is fine
        if response.status_code == 404:
            logger.warning("Subdomain %s was not registered (404), ignoring", subdomain)
            return

        raise
    except requests.exceptions.RequestException as e:
        logger.error("Caddy API request error during unregister: %s", e)
        logger.error("Failed to connect to Caddy API at %s", url)
        raise


def main() -> None:
    """CLI entrypoint for managing a Caddy subdomain."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Unregister instead of registering the subdomain",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore all persisted routes to Caddy",
    )
    parser.add_argument(
        "--list-persisted",
        action="store_true",
        help="List all persisted routes",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Don't persist this registration (temporary only)",
    )
    parser.add_argument(
        "--disable-auto-https",
        action="store_true",
        help="Skip configuring auto_https disable_redirects",
    )
    parser.add_argument(
        "--configure-auto-https-only",
        action="store_true",
        help="Only configure auto_https disable_redirects without registering routes",
    )
    args = parser.parse_args()

    caddy_host = os.environ.get("CADDY_HOST", "localhost:2019")

    # Handle special operations that don't require SUBDOMAIN
    if args.restore:
        restore_routes_from_persistence(caddy_host)
        return
        
    if args.list_persisted:
        routes = load_persisted_routes()
        if not routes:
            print("No persisted routes found")
        else:
            print(f"Found {len(routes)} persisted routes:")
            for subdomain, info in routes.items():
                print(f"  {subdomain} -> {info['target_address']} (registered: {info.get('registered_at', 'unknown')})")
        return

    if args.configure_auto_https_only:
        server_name = get_server_name(caddy_host)
        ensure_auto_https_config(caddy_host, server_name)
        print("auto_https disable_redirects configuration completed")
        return

    # For register/unregister operations, SUBDOMAIN is required
    subdomain = os.environ.get("SUBDOMAIN")
    if not subdomain:
        raise ValueError("SUBDOMAIN environment variable required")
    port = int(os.environ.get("PORT", "8000"))
    
    persist = not args.no_persist
    configure_auto_https = not args.disable_auto_https

    if args.remove:
        unregister_subdomain(subdomain, caddy_host, persist)
    else:
        register_subdomain(subdomain, port, caddy_host, persist, configure_auto_https)


if __name__ == "__main__":
    main()
