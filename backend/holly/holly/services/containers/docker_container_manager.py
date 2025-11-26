from typing import Any

import docker
from docker.errors import APIError
from docker.models.containers import Container
from loguru import logger

from holly.holly.services.containers.docker_network_manager import DockerNetworkManager


class DockerContainerManager:
    def __init__(self, network_manager: DockerNetworkManager):
        self.client = docker.from_env()
        self.network_manager = network_manager

    def start_container(
        self,
        image: str,
        container_name: str | None = None,
        ip_address: str | None = None,
        ports: list[int] | None = None,
        command: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Start a Docker container with specified parameters.

        Args:
            image: Docker image to use
            container_name: Optional name for the container
            ip_address: Static IP address (if None, one will be assigned)
            ports: List of ports to expose
            command: Optional command to run in the container
            environment: Dictionary of environment variables

        Returns:
            Dictionary with container info including ID and IP
        """
        try:
            # Pull the image if needed
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling image {image}...")
                self.client.images.pull(image)
                logger.info(f"Image {image} pulled successfully.")

            # Get next available IP if not specified
            if not ip_address:
                try:
                    ip_address = self.network_manager.get_next_available_ip()
                except Exception as e:
                    logger.error(f"Error getting IP address: {e!s}")
                    return None

            # Prepare port mappings - CHANGE: Use dynamic port mapping
            port_dict = {}
            if ports:
                for port in ports:
                    # Map container port to None for host port (dynamic assignment)
                    port_dict[f"{port}/tcp"] = None

            # Default command to None if not provided
            if not command:
                command = None

            # Start the container
            try:
                container = self.client.containers.run(
                    image=image,
                    name=container_name,
                    detach=True,
                    remove=True,  # Container will be removed when stopped
                    ports=port_dict if port_dict else None,
                    environment=environment,
                    command=command,
                    network=None,  # We'll connect it to the network separately to specify the IP
                )

                logger.info(f"connecting container {container.id} with IP {ip_address}")
                # Connect to the network with a specific IP
                while True:
                    try:
                        self.network_manager.network.connect(container=container.id, ipv4_address=ip_address)
                        break
                    except APIError as e:
                        if e.explanation == "Address already in use":
                            logger.info(f"{ip_address} is already in use, trying next available IP")
                            ip_address = increment_ip(ip_address)
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise

                # Get container details (including dynamically assigned ports)
                container_info = self.client.containers.get(container.id).attrs
                port_mappings = {}

                if "NetworkSettings" in container_info and "Ports" in container_info["NetworkSettings"]:
                    for port, bindings in container_info["NetworkSettings"]["Ports"].items():
                        if bindings:  # Not None
                            container_port = port.split("/")[0]
                            host_ip = bindings[0]["HostIp"] or "0.0.0.0"
                            host_port = bindings[0]["HostPort"]
                            port_mappings[container_port] = f"{host_ip}:{host_port}"

                return {
                    "container": container,
                    "id": container.id,
                    "ip_address": ip_address,
                    "port_mappings": port_mappings,
                    "exposed_ports": ports or [],
                }

            except APIError as e:
                if "Conflict" in str(e) and container_name:
                    logger.info(f"Container name '{container_name}' already in use. Removing and recreating...")
                    try:
                        existing = self.client.containers.get(container_name)
                        existing.stop()
                        existing.remove()
                        # Retry after removing
                        return self.start_container(image, container_name, ip_address, ports, command, environment)
                    except:
                        # If we can't remove, try with a different name
                        import random

                        new_name = f"{container_name}-{random.randint(1000, 9999)}"
                        logger.info(f"Using alternative name: {new_name}")
                        return self.start_container(image, new_name, ip_address, ports, command, environment)
                else:
                    logger.error(f"Error starting container: {e!s}")
                    return None

        except Exception as e:
            logger.error(f"Unexpected error starting container: {e!s}")
            return None

    def stop_container(self, container: Container | None) -> bool:
        """Stop a Docker container."""
        if not container:
            return False

        try:
            container.stop()
            logger.info(f"Container {container.id[:12]} stopped and removed.")
            return True
        except Exception as e:
            logger.error(f"Error stopping container: {e!s}")
            return False
