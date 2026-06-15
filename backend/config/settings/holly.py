"""
Holly container configuration settings
"""

import os

# Docker image for holly container
HOLLY_CONTAINER_IMAGE = os.environ.get("HOLLY_CONTAINER_IMAGE", "lingster/hilly:latest")

# Network name for holly containers
HOLLY_NETWORK = os.environ.get("HOLLY_NETWORK", "custom_holly_network")

# Container ports
HOLLY_API_PORT = int(os.environ.get("HOLLY_API_PORT", "8090"))
HOLLY_VNC_PORT = int(os.environ.get("HOLLY_VNC_PORT", "5901"))
HOLLY_NOVNC_PORT = int(os.environ.get("HOLLY_NOVNC_PORT", "6901"))

HOLLY_SUBNET = os.environ.get("HOLLY_SUBNET", "172.32.0.0/16")

# Timeout values
HOLLY_CONTAINER_STARTUP_TIMEOUT = int(os.environ.get("HOLLY_CONTAINER_STARTUP_TIMEOUT", "60"))

# Max number of containers per user
HOLLY_MAX_CONTAINERS_PER_USER = int(os.environ.get("HOLLY_MAX_CONTAINERS_PER_USER", "3"))

# Host for public access to containers (can be a domain name)
HOLLY_PUBLIC_HOST = os.environ.get("HOLLY_PUBLIC_HOST", "localhost")

# noVNC authentication settings
HOLLY_NOVNC_DEFAULT_USER = os.environ.get("HOLLY_NOVNC_DEFAULT_USER", "kasm_user")
HOLLY_NOVNC_DEFAULT_PASSWORD = os.environ.get("HOLLY_NOVNC_DEFAULT_PASSWORD", "vncpassword")

# Caddy reverse proxy settings
CADDY_API_URL = os.environ.get("CADDY_API_URL", "http://caddy:2019")
CADDY_DOMAIN_SUFFIX = os.environ.get("CADDY_DOMAIN_SUFFIX", "example.com")
# Only allow Caddy upstreams within the container network. This prevents the
# /caddy/map endpoint from being abused to proxy to internal/metadata addresses (SSRF).
CADDY_ALLOWED_UPSTREAM_NETWORK = os.environ.get("CADDY_ALLOWED_UPSTREAM_NETWORK", HOLLY_SUBNET)
# Working directory for aiagents webserver inside the container
HOLLY_WORKING_DIRECTORY = os.environ.get("HOLLY_WORKING_DIRECTORY", "/data")
