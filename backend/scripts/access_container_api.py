#!/usr/bin/env python3
"""
Script to access the REST API of a Holly container using its IP address and port.

This script demonstrates how to:
1. Retrieve the container IP address
2. Confirm the container is running
3. Access the REST API at http://<container_ip>:8090

Usage:
    python access_container_api.py <session_id>
"""

import sys
from pathlib import Path
from typing import tuple

import requests

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set up Django environment
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from loguru import logger

from holly.holly.services.containers.holly_container_service import HollyContainerService


def get_container_info(session_id: str) -> tuple[str | None, dict[str, int] | None]:
    """
    Get the IP address and ports for the container associated with the session.

    Args:
        session_id: ID of the Holly session

    Returns:
        Tuple containing (container_ip, ports_dict)
    """
    try:
        # Get the session model
        from holly.holly.models import HollySession  # Adjust this to match your actual session model

        # Get the session
        session = HollySession.objects.get(id=session_id)

        # Check if container exists
        if not session.container_id:
            logger.error(f"No container found for session {session_id}")
            return None, None

        # Initialize the Holly container service
        container_service = HollyContainerService()

        # Check if container is running
        if not container_service.is_container_running(session):
            logger.error(f"Container for session {session_id} is not running")
            return None, None

        # Get container IP address
        container_ip = container_service._get_container_ip(session.container_id)
        if not container_ip:
            logger.error(f"Could not get IP address for container {session.container_id}")
            return None, None

        # Get container ports
        ports = container_service.get_container_ports(session.container_id)
        if not ports:
            logger.error(f"Could not get ports for container {session.container_id}")
            return None, None

        return container_ip, ports

    except Exception as e:
        logger.exception(f"Error getting container info: {e}")
        return None, None


def access_rest_api(container_ip: str, rest_api_port: int, endpoint: str = "/health") -> bool:
    """
    Access the REST API on the container.

    Args:
        container_ip: IP address of the container
        rest_api_port: Port for the REST API
        endpoint: API endpoint to access

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"http://{container_ip}:{rest_api_port}{endpoint}"
        logger.info(f"Accessing REST API at: {url}")

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            logger.info(f"Successfully accessed REST API: {response.text}")
            return True
        logger.error(f"Failed to access REST API. Status code: {response.status_code}")
        return False

    except requests.RequestException as e:
        logger.error(f"Request error accessing REST API: {e}")
        return False


def main():
    """
    Main entry point for the script.
    """
    if len(sys.argv) < 2:
        sys.exit(1)

    session_id = sys.argv[1]
    logger.info(f"Getting container info for session: {session_id}")

    # Get container info
    container_ip, ports = get_container_info(session_id)

    if not container_ip or not ports:
        logger.error("Failed to get container information")
        sys.exit(1)

    logger.info(f"Container IP: {container_ip}")
    logger.info(f"Container ports: {ports}")

    # Access the REST API
    if "rest_api" in ports:
        rest_api_port = ports["rest_api"]
        logger.info(f"Accessing REST API on port: {rest_api_port}")

        # Try to access the health endpoint
        if access_rest_api(container_ip, rest_api_port):
            logger.info("Successfully accessed REST API!")
        else:
            logger.error("Failed to access REST API")

        # Example of accessing another endpoint
        logger.info("Trying to access a different endpoint...")
        access_rest_api(container_ip, rest_api_port, "/api/info")
    else:
        logger.error("REST API port not found in ports mapping")


if __name__ == "__main__":
    main()
