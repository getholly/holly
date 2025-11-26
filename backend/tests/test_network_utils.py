import ipaddress

import pytest

from holly.holly.services.containers import docker_network_manager, network_utils


def test_increment_subnet():
    assert network_utils.increment_subnet("192.168.1.0/24") == "192.168.2.0/24"


def test_increment_ip():
    assert network_utils.increment_ip("10.0.0.1") == "10.0.0.2"


def test_increment_ip_invalid():
    with pytest.raises(ValueError):
        network_utils.increment_ip("invalid")


def test_increment_subnet_invalid():
    with pytest.raises(ValueError):
        network_utils.increment_subnet("invalid")


def test_subnets_overlap():
    assert network_utils.subnets_overlap("10.0.0.0/24", "10.0.0.128/25") is True
    assert network_utils.subnets_overlap("192.168.1.0/24", "192.168.2.0/24") is False


class DummyNetwork:
    def __init__(self, id: str, name: str, subnet: str):
        self.id = id
        self.name = name
        gateway = str(ipaddress.ip_network(subnet)[1])
        self.attrs = {
            "IPAM": {"Config": [{"Subnet": subnet, "Gateway": gateway}]},
            "Driver": "bridge",
        }


class DummyNetworks:
    def __init__(self, networks):
        self._networks = networks

    def list(self):
        return self._networks

    def get(self, network_id):
        for net in self._networks:
            if net.id == network_id:
                return net
        raise ValueError("not found")


class ErrorNetworks(DummyNetworks):
    def get(self, network_id):
        raise network_utils.APIError("boom", None)


class DummyDockerClient:
    def __init__(self, networks):
        self.networks = DummyNetworks(networks)


def test_find_available_subnet_and_list_docker_networks():
    existing = [DummyNetwork("1", "net1", "192.168.100.0/24")]
    client = DummyDockerClient(existing)

    subnet = network_utils.find_available_subnet(client)
    assert subnet != "192.168.100.0/24"

    info = network_utils.list_docker_networks(client)
    assert info[0]["name"] == "net1"

    error_client = DummyDockerClient(existing)
    error_client.networks = ErrorNetworks(existing)
    info = network_utils.list_docker_networks(error_client)
    assert info[0]["subnet"] == "Error retrieving subnet"


def test_docker_network_manager_helpers():
    manager = docker_network_manager.DockerNetworkManager.__new__(docker_network_manager.DockerNetworkManager)
    manager.subnet = "172.32.0.0/30"
    manager.network = DummyNetwork("id", "net", "172.32.0.0/30")
    manager.client = DummyDockerClient([manager.network])
    manager._used_ips = set()

    gateway = manager.get_network_gateway()
    assert gateway == "172.32.0.1"

    ip = manager.get_next_available_ip()
    assert ip == "172.32.0.2"
