import ipaddress

import docker
from docker.errors import APIError


def increment_subnet(subnet_str):
    try:
        network = ipaddress.IPv4Network(subnet_str, strict=True)
        next_network = ipaddress.IPv4Network((int(network.network_address) + network.num_addresses, network.prefixlen))
        return str(next_network)
    except ValueError as e:
        msg = f"Invalid subnet: {e}"
        raise ValueError(msg)


def increment_ip(ip_str):
    try:
        ip = ipaddress.IPv4Address(ip_str)
        next_ip = ip + 1
        return str(next_ip)
    except ipaddress.AddressValueError:
        raise ValueError("Invalid IP address format")


def subnets_overlap(subnet1: str, subnet2: str) -> bool:
    """Check if two subnets overlap."""
    try:
        net1 = ipaddress.IPv4Network(subnet1, strict=False)
        net2 = ipaddress.IPv4Network(subnet2, strict=False)
        return net1.overlaps(net2)
    except ValueError:
        # If we can't parse one of the subnets, assume they don't overlap
        return False


def find_available_subnet(docker_client=None) -> str:
    """
    Find an available subnet that doesn't overlap with existing Docker networks.

    Args:
        docker_client: Optional Docker client instance. If None, a new one will be created.

    Returns:
        A string representing an available subnet in CIDR notation
    """
    if docker_client is None:
        docker_client = docker.from_env()

    # Get all existing networks
    networks = docker_client.networks.list()
    used_subnets = []

    for network in networks:
        try:
            network_details = docker_client.networks.get(network.id).attrs
            if "IPAM" in network_details and "Config" in network_details["IPAM"]:
                if network_details["IPAM"]["Config"] is not None:  # Check for None
                    for config in network_details["IPAM"]["Config"]:
                        if "Subnet" in config:
                            used_subnets.append(config["Subnet"])
        except (APIError, KeyError, TypeError):
            # Skip networks we can't inspect
            continue

    # List of common private subnets to try
    possible_subnets = [
        "192.168.100.0/24",
        "192.168.101.0/24",
        "192.168.102.0/24",
        "172.20.0.0/16",
        "172.21.0.0/16",
        "172.22.0.0/16",
        "10.10.0.0/16",
        "10.11.0.0/16",
        "10.12.0.0/16",
    ]

    # Find the first non-overlapping subnet
    for candidate in possible_subnets:
        ipaddress.IPv4Network(candidate)
        if not any(subnets_overlap(candidate, used) for used in used_subnets):
            return candidate

    # If all common subnets are used, create a random one in 10.0.0.0/8
    for i in range(20, 255):
        for j in range(255):
            candidate = f"10.{i}.{j}.0/24"
            if not any(subnets_overlap(candidate, used) for used in used_subnets):
                return candidate

    raise Exception("Could not find an available subnet. Please specify a subnet manually.")


def list_docker_networks(docker_client=None) -> list[dict[str, str]]:
    """
    List all Docker networks with their subnet information.

    Args:
        docker_client: Optional Docker client instance. If None, a new one will be created.

    Returns:
        A list of dictionaries with network information
    """
    if docker_client is None:
        docker_client = docker.from_env()

    networks = docker_client.networks.list()
    network_info = []

    for network in networks:
        try:
            network_details = docker_client.networks.get(network.id).attrs
            subnet = "N/A"
            if "IPAM" in network_details and "Config" in network_details["IPAM"]:
                if network_details["IPAM"]["Config"]:  # Check if not None or empty
                    subnet = network_details["IPAM"]["Config"][0].get("Subnet", "N/A")

            network_info.append(
                {
                    "name": network.name,
                    "id": network.id,
                    "subnet": subnet,
                    "driver": network_details.get("Driver", "N/A"),
                }
            )
        except (APIError, KeyError):
            # Skip networks we can't inspect
            network_info.append(
                {"name": network.name, "id": network.id, "subnet": "Error retrieving subnet", "driver": "N/A"}
            )

    return network_info
