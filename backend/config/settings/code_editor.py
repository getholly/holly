"""
Code Editor container configuration settings
"""

import os

# Docker image for code editor container
CODE_EDITOR_CONTAINER_IMAGE = os.environ.get("CODE_EDITOR_CONTAINER_IMAGE", "code-editor-container:latest")

# Network name for code editor containers
CODE_EDITOR_NETWORK = os.environ.get("CODE_EDITOR_NETWORK", "code_editor_network")

# Container API port
CODE_EDITOR_CONTAINER_PORT = int(os.environ.get("CODE_EDITOR_CONTAINER_PORT", "8000"))

# Timeout values
CODE_EDITOR_CONTAINER_STARTUP_TIMEOUT = int(os.environ.get("CODE_EDITOR_CONTAINER_STARTUP_TIMEOUT", "60"))
CODE_EDITOR_PROMPT_TIMEOUT = int(os.environ.get("CODE_EDITOR_PROMPT_TIMEOUT", "120"))

# Max number of containers per user
CODE_EDITOR_MAX_CONTAINERS_PER_USER = int(os.environ.get("CODE_EDITOR_MAX_CONTAINERS_PER_USER", "3"))

# Host for public access to containers (can be a domain name)
CODE_EDITOR_PUBLIC_HOST = os.environ.get("CODE_EDITOR_PUBLIC_HOST", "localhost")

# Claude VNC Container settings
USE_CLAUDE_CONTAINER = os.environ.get("USE_CLAUDE_CONTAINER", "True").lower() in ("true", "1", "yes")
CLAUDE_EDITOR_CONTAINER_IMAGE = os.environ.get("CLAUDE_EDITOR_CONTAINER_IMAGE", "lingster/hilly:latest")
CLAUDE_EDITOR_API_PORT = int(os.environ.get("CLAUDE_EDITOR_API_PORT", "8002"))
CLAUDE_EDITOR_VNC_PORT = int(os.environ.get("CLAUDE_EDITOR_VNC_PORT", "5901"))
CLAUDE_EDITOR_NOVNC_PORT = int(os.environ.get("CLAUDE_EDITOR_NOVNC_PORT", "6080"))

# noVNC authentication settings
NOVNC_DEFAULT_USER = os.environ.get("NOVNC_DEFAULT_USER", "kasm_user")
NOVNC_DEFAULT_PASSWORD = os.environ.get("NOVNC_DEFAULT_PASSWORD", "vncpassword")

# Set a more reliable path for the aiagent code
# The path will be computed dynamically in the ContainerService class
# This is just a fallback
CLAUDE_EDITOR_AIAGENT_PATH = os.environ.get("CLAUDE_EDITOR_AIAGENT_PATH", None)
