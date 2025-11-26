import ipaddress

import docker
from docker.errors import APIError
from docker.models.networks import Network
from loguru import logger

from holly.holly.services.containers.network_utils import find_available_subnet


class DockerNetworkManager:
    def __init__(self, network_name: str = "custom_network", subnet: str = "10.10.0.0/16"):
        self.client = docker.from_env()
        self.network_name = network_name
        self.subnet = subnet
        self.network = self._ensure_network_exists()
        self._used_ips: set[str] = set()
        self._refresh_used_ips()

    def _ensure_network_exists(self) -> Network:
        """Ensure the specified network exists, create if it doesn't."""
        try:
            networks = self.client.networks.list(names=[self.network_name])

            if networks:
                network = networks[0]
                logger.info(f"Network {self.network_name} already exists.")

                # Check if the subnet matches
                network_details = self.client.networks.get(network.id).attrs
                if (
                    "IPAM" in network_details
                    and "Config" in network_details["IPAM"]
                    and network_details["IPAM"]["Config"]
                ):
                    existing_subnet = network_details["IPAM"]["Config"][0].get("Subnet")
                    if existing_subnet and existing_subnet != self.subnet:
                        logger.info(
                            f"Warning: Network exists with subnet {existing_subnet}, "
                            f"which differs from requested subnet {self.subnet}. "
                            f"Using existing subnet."
                        )
                        self.subnet = existing_subnet

                return network

            # If we're here, we need to create the network
            try:
                ipam_pool = docker.types.IPAMPool(subnet=self.subnet)
                ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

                network = self.client.networks.create(name=self.network_name, driver="bridge", ipam=ipam_config)
                logger.info(f"Network {self.network_name} created successfully with subnet {self.subnet}.")
                return network

            except APIError as e:
                if "Pool overlaps" in str(e):
                    logger.info(f"Subnet {self.subnet} overlaps with an existing network.")
                    new_subnet = find_available_subnet(self.client)
                    logger.info(f"Using alternative subnet: {new_subnet}")
                    self.subnet = new_subnet

                    ipam_pool = docker.types.IPAMPool(subnet=new_subnet)
                    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

                    network = self.client.networks.create(name=self.network_name, driver="bridge", ipam=ipam_config)
                    logger.info(f"Network {self.network_name} created successfully with subnet {new_subnet}.")
                    return network
                raise

        except Exception as e:
            logger.error(f"Error setting up network: {e!s}")
            raise

    def _refresh_used_ips(self) -> None:
        """Refresh the list of used IPs in the network."""
        self._used_ips = set()

        try:
            # Get detailed network info
            network_info = self.client.networks.get(self.network.id).attrs

            # Extract currently used IPs from containers
            if "Containers" in network_info:
                for container_info in network_info["Containers"].values():
                    if "IPv4Address" in container_info:
                        # Extract IP without CIDR notation
                        ip = container_info["IPv4Address"].split("/")[0]
                        self._used_ips.add(ip)
        except Exception as e:
            logger.error(f"Warning: Could not refresh used IPs: {e!s}")

    def get_network_gateway(self) -> str:
        """Get the gateway IP of the network."""
        try:
            network_info = self.client.networks.get(self.network.id).attrs
            if "IPAM" in network_info and "Config" in network_info["IPAM"] and network_info["IPAM"]["Config"]:
                return network_info["IPAM"]["Config"][0].get("Gateway", "")
        except Exception:
            pass

        # If we can't get the gateway from the network, calculate it
        # It's usually the first host address in the subnet
        network = ipaddress.IPv4Network(self.subnet, strict=False)
        return str(next(iter(network.hosts())))

    def get_next_available_ip(self) -> str:
        """Get the next available IP address in the subnet."""
        self._refresh_used_ips()

        # Parse the subnet to get network address and prefixlen
        network = ipaddress.IPv4Network(self.subnet, strict=False)
        gateway = self.get_network_gateway()

        # Skip the network address, gateway, and broadcast address
        for ip in network.hosts():
            ip_str = str(ip)
            if ip_str == gateway:
                continue

            if ip_str not in self._used_ips:
                return ip_str

        msg = f"No available IP addresses in the subnet {self.subnet}"
        raise Exception(msg)

    def get_all_used_ips(self) -> set[str]:
        """Get all currently used IPs in the network."""
        self._refresh_used_ips()
        return self._used_ips
