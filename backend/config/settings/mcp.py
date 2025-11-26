# REST MCP Client Settings
# ------------------------------------------------------------------------------
import os

# Base URL for the REST MCP server
REST_MCP_SERVER_URL = os.environ.get("REST_MCP_SERVER_URL", "http://localhost")

# Port for the REST MCP server, leave empty for default HTTP port
REST_MCP_SERVER_PORT = os.environ.get("REST_MCP_SERVER_PORT", "8090")

# Timeout for REST MCP requests in seconds (increased for slow container initialization)
REST_MCP_REQUEST_TIMEOUT = int(os.environ.get("REST_MCP_REQUEST_TIMEOUT", "180"))

# Timeout for REST MCP health check requests in seconds
REST_MCP_HEALTH_CHECK_TIMEOUT = int(os.environ.get("REST_MCP_HEALTH_CHECK_TIMEOUT", "30"))

# Whether to verify SSL certificates when connecting to REST MCP server
REST_MCP_VERIFY_SSL = os.environ.get("REST_MCP_VERIFY_SSL", "True").lower() == "true"

# if true don't use container for requests
REST_MCP_SERVER_LOCAL = os.environ.get("REST_MCP_SERVER_LOCAL", False)

# Complete URL for REST MCP server (constructed from the above settings)
REST_MCP_BASE_URL = f"{REST_MCP_SERVER_URL}:{REST_MCP_SERVER_PORT}" if REST_MCP_SERVER_PORT else REST_MCP_SERVER_URL
