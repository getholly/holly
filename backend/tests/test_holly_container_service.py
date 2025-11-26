import unittest
from types import SimpleNamespace
from unittest import mock

import docker

from holly.holly.services.containers import holly_container_service
from holly.holly.services.containers.holly_container_service import HollyContainerService


class MockContainer:
    def __init__(self, id="test-container-id", status="running"):
        self.id = id
        self.status = status
        self.attrs = {
            "NetworkSettings": {
                "Networks": {"holly_network": {"IPAddress": "172.17.0.2"}},
                "Ports": {
                    "8005/tcp": [{"HostPort": "8005"}],
                    "5902/tcp": [{"HostPort": "5902"}],
                    "6081/tcp": [{"HostPort": "6081"}],
                    "8090/tcp": [{"HostPort": "8090"}],
                    "6901/tcp": [{"HostPort": "6901"}],
                },
            }
        }

    def reload(self):
        pass

    def stop(self, timeout=None):
        pass

    def remove(self, force=None):
        pass


class MockSession:
    def __init__(self, id="test-session", container_id=None):
        self.id = id
        self.container_id = container_id

    def save(self):
        pass


class MockDockerClient:
    def __init__(self):
        self.containers = MockContainers()
        self.networks = MockNetworks()


class StubNetworkManager:
    def __init__(self):
        self.network = SimpleNamespace(connect=lambda container=None, ipv4_address=None: None)

    def get_next_available_ip(self):
        return "172.32.0.2"


class StubContainerManager:
    pass


class MockContainers:
    def __init__(self):
        self.containers = {}

    def get(self, container_id):
        if container_id not in self.containers:
            raise docker.errors.NotFound("Container not found")
        return self.containers[container_id]

    def list(self, filters=None):
        return list(self.containers.values())

    def run(self, image, **kwargs):
        container = MockContainer()
        self.containers[container.id] = container
        return container


class MockNetworks:
    def __init__(self):
        self.networks = {}

    def list(self, names=None):
        return list(self.networks.values())

    def create(self, name, driver=None):
        self.networks[name] = {"name": name, "driver": driver}
        return self.networks[name]


@mock.patch("docker.from_env")
class HollyContainerServiceTest(unittest.TestCase):
    def setUp(self):
        HollyContainerService._instance = None
        HollyContainerService._initialized = False
        self.mock_docker_client = MockDockerClient()
        self.mock_session = MockSession()
        self.stub_network_manager = StubNetworkManager()
        holly_container_service.DockerNetworkManager = lambda name, subnet: self.stub_network_manager
        holly_container_service.DockerContainerManager = lambda network_manager: StubContainerManager()
        holly_container_service.settings = SimpleNamespace(
            HOLLY_CONTAINER_IMAGE="test_image",
            HOLLY_API_PORT=8090,
            HOLLY_VNC_PORT=5901,
            HOLLY_NOVNC_PORT=6901,
            HOLLY_NETWORK="holly_network",
            HOLLY_SUBNET="172.32.0.0/16",
        )

    def test_init(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()

        # Verify that both new ports are initialized
        assert service.rest_api_port == 8090
        assert service.novnc_port == 6901

    def test_start_container_with_explicit_ports(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()

        # Mock the container.run call to capture the ports argument
        with mock.patch.object(self.mock_docker_client.containers, "run") as mock_run:
            mock_container = MockContainer()
            mock_run.return_value = mock_container

            service.start_container(self.mock_session, "test-token")

            # Verify that the ports are explicitly mapped
            ports_arg = mock_run.call_args.kwargs.get("ports", {})

            # Check that our new ports are included with explicit mappings
            assert f"{service.rest_api_port}/tcp" in ports_arg
            assert f"{service.novnc_port}/tcp" in ports_arg

            # Verify that the explicit port mapping is set correctly
            assert ports_arg[f"{service.rest_api_port}/tcp"] is None
            assert ports_arg[f"{service.novnc_port}/tcp"] is None

    def test_get_container_ports_includes_new_ports(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()

        # Create a mock container and add it to the client
        mock_container = MockContainer()
        self.mock_docker_client.containers.containers[mock_container.id] = mock_container

        # Call get_container_ports
        ports = service.get_container_ports(mock_container.id)

        # Verify that the new ports are included in the result
        assert "rest_api" in ports
        assert "novnc" in ports

        # Verify port values
        assert ports["rest_api"] == 8090
        assert ports["novnc"] == 6901

    def test_is_container_running(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()
        container = MockContainer()
        self.mock_docker_client.containers.containers[container.id] = container
        self.mock_session.container_id = container.id

        assert service.is_container_running(self.mock_session)

    def test_get_container_ip(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()
        container = MockContainer()
        self.mock_docker_client.containers.containers[container.id] = container

        ip = service._get_container_ip(container.id)
        assert ip == "172.17.0.2"

    def test_get_docker_external_port(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()
        container = MockContainer()

        port = service._get_docker_external_port(container, 8090)
        assert port == 8090

    def test_is_container_running_not_found(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()
        self.mock_session.container_id = "missing"

        assert not service.is_container_running(self.mock_session)

    def test_get_container_ports_not_found(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()

        ports = service.get_container_ports("missing")
        assert ports == {}

    def test_get_docker_external_port_missing(self, mock_docker_from_env):
        mock_docker_from_env.return_value = self.mock_docker_client

        service = HollyContainerService()
        container = MockContainer()
        assert service._get_docker_external_port(container, 9999) is None


if __name__ == "__main__":
    unittest.main()
