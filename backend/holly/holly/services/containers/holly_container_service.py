import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import docker
import requests
from django.conf import settings
from docker.errors import APIError
from loguru import logger
from pydantic import BaseModel

from holly.holly.services.common.errors import ContainerStartError, NetworkCreateError
from holly.holly.services.containers.docker_container_manager import DockerContainerManager
from holly.holly.services.containers.docker_network_manager import DockerNetworkManager
from holly.holly.services.containers.network_utils import increment_ip

if TYPE_CHECKING:
    from holly.holly.models.mission import Mission


class ContainerDetails(BaseModel):
    container_id: str
    port_mappings: dict[int, int]
    ip_address: str


class ContainerServiceInterface(Protocol):
    """Protocol for container service implementations."""

    def start_container(self, session: "Mission", auth_token: str) -> str: ...

    def stop_container(self, session: "Mission") -> bool: ...

    def is_container_running(self, session: "Mission") -> bool: ...

    def get_container_ports(self, container_id: str) -> dict[str, int]: ...


class HollyContainerService(ContainerServiceInterface):
    """Service for managing Holly Docker containers.

    This class is implemented as a singleton to ensure only one instance exists.
    """

    # Singleton instance
    _instance = None
    _initialized = False

    # HTTP status code for successful responses
    HTTP_OK = 200
    # Flag to determine whether to use localhost ports for connections
    USE_LOCAL_PORTS = True

    def __new__(cls):
        """Create a new instance of the class if one doesn't exist."""
        if cls._instance is None:
            logger.debug("Creating new HollyContainerService instance")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the Holly container service."""
        # Skip initialization if already initialized
        if self._initialized:
            logger.debug("HollyContainerService already initialized, skipping")
            return

        self.client: docker.DockerClient = docker.from_env()
        self.container_image: str = settings.HOLLY_CONTAINER_IMAGE
        self.api_port: int = settings.HOLLY_API_PORT
        self.vnc_port: int = settings.HOLLY_VNC_PORT
        self.novnc_port: int = settings.HOLLY_NOVNC_PORT

        # Add specific ports for REST API and VNC web access
        self.rest_api_port: int = settings.HOLLY_API_PORT

        self.network_name: str = settings.HOLLY_NETWORK

        logger.info(f"Using container image: {self.container_image}")
        logger.info(f"API port: {self.api_port}, VNC port: {self.vnc_port}, noVNC port: {self.novnc_port}")
        logger.info(f"REST API port: {self.rest_api_port}")  # , VNC Web port: {self.vnc_web_port}")
        logger.info(f"Network name: {self.network_name}")

        self.network_manager = None
        self.container_manager = None

        self.setup(self.network_name, settings.HOLLY_SUBNET)
        # self._ensure_network()

        # Mark as initialized to prevent further initialization
        HollyContainerService._initialized = True

    def setup(self, network_name: str, subnet: str) -> bool:
        """Set up network and container managers."""
        try:
            self.network_manager = DockerNetworkManager(network_name, subnet)
            self.container_manager = DockerContainerManager(self.network_manager)
            return True
        except Exception as e:
            logger.error(f"Failed to set up container orchestration: {e!s}")
            return False

    def _ensure_network(self) -> None:
        """
        Ensure the Docker network exists.

        Raises:
            NetworkCreateError: If the network cannot be created
        """
        try:
            networks = self.client.networks.list(names=[self.network_name])
            if not networks:
                logger.info(f"Creating Docker network: {self.network_name}")
                self.client.networks.create(self.network_name, driver="bridge")
        except Exception as e:
            logger.error(f"Error ensuring Docker network: {e}")
            raise NetworkCreateError from e

    def start_container(self, session: "Mission", auth_token: str, environment: dict[str, str]) -> str:  # noqa: C901
        """
        Start a new Holly container for a mission session.

        Args:
            session: The session object with id and container_id attributes
            auth_token: Authentication token
            environment: Dictionary of environment variables

        Returns:
            str: The container ID if successful

        Raises:
            ContainerStartError: If the container cannot be started
        """
        session_id = str(session.id)
        environment.update({"SESSION_ID": session_id, "AUTH_TOKEN": auth_token})
        container_name = f"holly-container-{session_id}"
        workdir = Path(f"/tmp/holly-container-{session_id}")  # noqa: S108

        # Check if the container already exists and is running
        if session.container_id and self.is_container_running(session):
            logger.info(f"Container already running: {session.container_id}")
            return session.container_id

        try:
            # Check if the container already exists but isn't assigned to the session
            try:
                logger.info(f"Starting container: {container_name}")
                existing_container = self.client.containers.get(container_name)
                if existing_container.status in ["running", "created"]:
                    logger.info(
                        f"Container {container_name}/{existing_container.id} already exists and is {existing_container.status}"
                    )
                    # Update session with container ID
                    session.container_id = existing_container.id
                    session.save()
                    return existing_container.id
            except docker.errors.NotFound:
                pass  # Container doesn't exist, continue with creation

            # Create temp directory for this session
            workdir.mkdir(parents=True, exist_ok=True)

            # Set up volume configuration
            volumes = {}

            # Create container with explicit port mappings and appropriate volumes and environment variables
            # Use fixed port mappings for predictable access
            container = self.client.containers.run(
                self.container_image,
                detach=True,
                environment=environment,
                network=None,
                name=container_name,
                volumes=volumes,
                ports={
                    # Use explicit host port mapping for predictable access
                    f"{self.api_port}/tcp": None,  # Map to same port on host
                    f"{self.vnc_port}/tcp": None,  # Map to same port on host
                    f"{self.novnc_port}/tcp": None,  # Map to same port on host
                    f"{self.rest_api_port}/tcp": None,  # REST API port
                    # f"{self.vnc_web_port}/tcp": self.vnc_web_port,  # VNC Web port
                },
                labels={
                    "app": "holly",
                    "session_id": session_id,
                },
                restart_policy={"Name": "unless-stopped"},
            )

            # Now connect up to a network and set ip address:
            try:
                ip_address = self.network_manager.get_next_available_ip()
            except Exception as e:
                logger.error(f"Error getting IP address: {e!s}")
                return None

            retries = 10
            while True and retries > 0:
                try:
                    self.network_manager.network.connect(container=container.id, ipv4_address=ip_address)
                    logger.info(f"container connected with {ip_address=}/{container.id[:12]}")
                    break
                except APIError as e:
                    if e.explanation == "Address already in use":
                        logger.info(f"{ip_address} is already in use, trying next available IP")
                        ip_address = increment_ip(ip_address)
                        retries -= 1
                    else:
                        logger.error(f"Error connecting container to network: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise

            # allow a short time for the container to startup
            retries = 5
            while retries > 0:
                status = container.status
                if status == "running":
                    break
                time.sleep(1)
                retries -= 1

            # Update session with container ID
            container_id = container.id
            session.container_id = container_id
            session.save()

            # Wait for container API to be ready
            if not self._wait_for_container_ready(container_id):
                error_message = "Container started but REST API failed to become ready"
                logger.error(error_message)
                raise ContainerStartError(error_message)

            logger.info(f"Started container: {container_id}")
            return container_id

        except docker.errors.APIError as e:
            error_message = f"Docker API error: {e}"
            logger.exception(f"Docker API error when starting container: {e}")
            raise ContainerStartError(error_message) from e

        except docker.errors.ImageNotFound as e:
            error_message = f"Docker image not found: {e}"
            logger.exception(f"Docker image not found: {e}")
            raise ContainerStartError(error_message) from e

        except (docker.errors.BuildError, docker.errors.ContainerError) as e:
            error_message = f"Docker container error: {e}"
            logger.exception(f"Docker container error: {e}")
            raise ContainerStartError(error_message) from e

        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.exception(f"Unexpected error starting container: {e}")
            raise ContainerStartError(error_message) from e
        finally:
            if not session.container_id:
                self.stop_container(session)
                if workdir.exists():
                    shutil.rmtree(workdir, ignore_errors=True)
        raise ContainerStartError

    def get_port_mappings(self, container_id) -> dict[str, str]:
        container_info = self.client.containers.get(container_id).attrs
        port_mappings = {}

        if "NetworkSettings" in container_info and "Ports" in container_info["NetworkSettings"]:
            for port, bindings in container_info["NetworkSettings"]["Ports"].items():
                if bindings:  # Not None
                    container_port = port.split("/")[0]
                    host_ip = bindings[0]["HostIp"] or "0.0.0.0"
                    host_port = bindings[0]["HostPort"]
                    port_mappings[container_port] = f"{host_ip}:{host_port}"
        return port_mappings

    def get_container_ip(self, container_id: str) -> str | None:
        """Get container IP address, prioritizing custom networks over default bridge."""
        try:
            container_info = self.client.containers.get(container_id).attrs

            # FIRST check custom networks (172.32.x.x)
            networks = container_info["NetworkSettings"]["Networks"]
            for network_name, network_data in networks.items():
                # Skip default bridge network
                if network_name != "bridge":
                    ip_address = network_data.get("IPAddress")
                    if ip_address:
                        logger.info(f"Found container IP {ip_address} on network {network_name}")
                        return ip_address

            # FALLBACK to default bridge network
            ip_address = container_info["NetworkSettings"]["IPAddress"]
            if ip_address:
                logger.warning(f"Using default bridge IP {ip_address} (may not be accessible)")
                return ip_address

            logger.error(f"Could not find IP address for container {container_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting container IP: {e}")
            return None

    def stop_container(self, session: "Mission") -> bool:
        """
        Stop and remove a container.

        Args:
            session: The session object with id and container_id attributes

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not session.container_id:
            logger.warning(f"No container ID found for session {session.id}")
            return True

        success = True
        workdir = Path(f"/tmp/holly-container-{session.id}")  # noqa: S108

        try:
            container = self.client.containers.get(session.container_id)

            # Clean up temp directory if it exists
            if workdir.exists():
                logger.info(f"Cleaning up temp directory: {workdir}")
                shutil.rmtree(workdir, ignore_errors=True)

            # Stop the container
            logger.info(f"Stopping container: {session.container_id}")
            container.stop(timeout=5)
            container.remove(force=True)
        except docker.errors.NotFound:
            logger.info(f"Container already removed: {session.container_id}")
        except docker.errors.APIError as e:
            logger.error(f"Docker API error stopping container: {e}")
            success = False
        except (docker.errors.BuildError, docker.errors.ContainerError) as e:
            logger.error(f"Docker container error when stopping: {e}")
            success = False

        # Clean up session if successful
        if success:
            session.container_id = None
            session.save()

        return success

    def is_container_running(self, session: "Mission") -> bool:
        """
        Check if the container for the session is running.

        Args:
            session: The session object with container_id attribute

        Returns:
            bool: True if container is running, False otherwise
        """
        if not session.container_id:
            return False

        status = None
        try:
            container = self.client.containers.get(session.container_id)
            container.reload()
            status = container.status
        except docker.errors.NotFound:
            logger.warning(f"Container {session.container_id} not found.")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Docker API error checking container state: {e}")
            return False
        except (docker.errors.BuildError, docker.errors.ContainerError) as e:
            logger.error(f"Docker container error when checking status: {e}")
            return False

        return status == "running"

    def _wait_for_container_ready(self, container_id: str, max_retries: int = 15, wait_seconds: int = 2) -> bool:
        """
        Wait for the container API to be ready.

        Args:
            container_id: The container ID
            max_retries: Maximum number of retry attempts
            wait_seconds: Seconds to wait between retries

        Returns:
            bool: True if container is ready, False otherwise
        """
        logger.info(f"Waiting for container {container_id} API to be ready (max {max_retries} retries)...")
        container = self.client.containers.get(container_id)

        for attempt in range(1, max_retries + 1):
            try:
                # Check if container is still running
                container.reload()
                if container.status != "running":
                    logger.error(f"Container {container_id} is not running. Status: {container.status}")
                    return False

                # Get container IP address
                container_ip = self._get_container_ip(container_id)
                if not container_ip:
                    logger.warning(
                        f"Could not get IP address for container {container_id}, attempt {attempt}/{max_retries}..."
                    )
                    time.sleep(wait_seconds)
                    continue

                external_port = self._get_docker_external_port(container, self.api_port)
                if not external_port:
                    logger.warning(f"Could not get external port for container, attempt {attempt}/{max_retries}")
                    time.sleep(wait_seconds)
                    continue

                # Try to connect to the container API
                health_check_ip = "127.0.0.1" if self.USE_LOCAL_PORTS else container_ip
                logger.info(f"Trying to connect to API at http://{health_check_ip}:{external_port}/api/health")
                response = requests.get(f"http://{health_check_ip}:{external_port}/api/health", timeout=5)

                if response.status_code == self.HTTP_OK:
                    logger.info(f"Container API is ready: {container_id}")
                    # Log response content for debugging
                    logger.info(f"Health check response: {response.text}")
                    return True

                logger.warning(f"Health check returned non-200 status: {response.status_code}")

            except requests.RequestException as e:
                logger.warning(f"Container API not ready yet (attempt {attempt}/{max_retries}): {e!s}")

            time.sleep(wait_seconds)

        logger.error(f"Container API failed to become ready after {max_retries} attempts")
        return False

    def _get_container_ip(self, container_id: str) -> str | None:
        """
        Get the IP address of a container.

        Args:
            container_id: The container ID

        Returns:
            Optional[str]: Container IP address or None if not found
        """
        try:
            container = self.client.containers.get(container_id)
            networks_data = container.attrs.get("NetworkSettings", {}).get("Networks", {})

            # First check our preferred network
            if self.network_name in networks_data:
                return networks_data[self.network_name].get("IPAddress")

            # Fallback: check all networks
            for config in networks_data.values():
                ip = config.get("IPAddress")
                if ip:
                    return ip

        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found when getting IP")
        except docker.errors.APIError as e:
            logger.error(f"Docker API error getting container IP: {e}")
        except (docker.errors.BuildError, docker.errors.ContainerError) as e:
            logger.error(f"Docker container error when getting IP: {e}")
        return None

    def _get_docker_external_port(self, container: docker.models.containers.Container, port: int) -> int | None:
        """
        Get the external port mapped to the specified internal port of a Docker container.

        Args:
            container: The Docker container
            port: The internal port to find mapping for

        Returns:
            Optional[int]: The external port or None if not found
        """
        try:
            port_mappings = container.attrs["NetworkSettings"]["Ports"]
            port_key = f"{port}/tcp"

            if port_mappings.get(port_key):
                return int(port_mappings[port_key][0]["HostPort"])
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error getting external port mapping: {e}")
            return None
        return None

    def get_container_ports(self, container_id: str) -> dict[str, int]:
        """
        Get the mapped ports for a container.

        Args:
            container_id: The container ID

        Returns:
            dict: Mapping of service names to port numbers
        """
        try:
            container = self.client.containers.get(container_id)
            ports = {}

            port_mappings = container.attrs["NetworkSettings"]["Ports"]

            # Extract the host port for API
            api_port_key = f"{self.api_port}/tcp"
            if port_mappings.get(api_port_key):
                ports["api"] = int(port_mappings[api_port_key][0]["HostPort"])

            # Extract the host port for VNC
            vnc_port_key = f"{self.vnc_port}/tcp"
            if port_mappings.get(vnc_port_key):
                ports["vnc"] = int(port_mappings[vnc_port_key][0]["HostPort"])

            # Extract the host port for noVNC
            novnc_port_key = f"{self.novnc_port}/tcp"
            if port_mappings.get(novnc_port_key):
                ports["novnc"] = int(port_mappings[novnc_port_key][0]["HostPort"])

            # Extract the host port for REST API
            rest_api_port_key = f"{self.rest_api_port}/tcp"
            if port_mappings.get(rest_api_port_key):
                ports["rest_api"] = int(port_mappings[rest_api_port_key][0]["HostPort"])

            # Extract the host port for VNC Web
            # vnc_web_port_key = f"{self.vnc_web_port}/tcp"
            # if port_mappings.get(vnc_web_port_key):
            # ports["vnc_web"] = int(port_mappings[vnc_web_port_key][0]["HostPort"])

        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found when getting ports")
            return {}
        except docker.errors.APIError as e:
            logger.error(f"Docker API error getting container ports: {e}")
            return {}
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error getting container ports: {e}")
            return {}
        return ports
