"""
Common exception classes for container services.
"""


class NetworkCreateError(Exception):
    """Error occurred when creating Docker network"""


class ContainerStartError(Exception):
    """Error occurred when starting a container"""


class ContainerStopError(Exception):
    """Error occurred when stopping a container"""


class ContainerStatusError(Exception):
    """Error occurred when checking container status"""


class ContainerIPError(Exception):
    """Error occurred when getting container IP address"""


class NoContainerError(Exception):
    """No active container for the session"""


class PromptDeliveryError(Exception):
    """Error occurred when sending prompt to container"""


class NoExternalPortError(Exception):
    """Error occurred when getting external port mapping"""
