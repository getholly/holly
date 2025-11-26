# Accessing Container REST API

This guide explains how to configure and access the REST API service running inside a Docker container using its IP address and port.

## Configuration

The Holly container service has been configured to use a bridge network with explicit port mappings, allowing you to access container services like the REST API using the container's IP address and port.

### Key Ports

The following ports are exposed:

- **REST API**: 8090
- **VNC Web**: 6901
- **API**: 8005 (Holly API)
- **VNC**: 5902
- **noVNC**: 6081

## Usage

### Finding the Container IP and Ports

You can use the `access_container_api.py` script to find the IP address and ports of a container for a specific session:

```bash
python scripts/access_container_api.py <session_id>
```

This will:
1. Find the container associated with the session
2. Check if the container is running
3. Get the container's IP address and ports
4. Try to access the REST API

### Accessing the REST API Directly

Once you have the container IP and port, you can access the REST API using:

```
http://<container_ip>:8090/endpoint
```

For example:
```
http://172.17.0.2:8090/health
```

### From Code

To access the REST API from your code, use the following pattern:

```python
import requests

# Get container IP (from HollyContainerService._get_container_ip)
container_ip = "172.17.0.2"  # Example IP

# REST API port is 8090
api_url = f"http://{container_ip}:8090/your-endpoint"

# Make the request
response = requests.get(api_url)

# Process the response
if response.status_code == 200:
    data = response.json()
    # Process data...
```

## Debugging

If you're unable to connect to the REST API:

1. Ensure the container is running
2. Verify the bridge network is properly configured
3. Check that the REST API service inside the container is active
4. Verify that the port is exposed and mapped correctly
5. Check firewall settings if applicable

## Docker Network Details

The Holly containers use a bridge network named `holly_network`. This provides:

- Network isolation between containers
- Communication between containers on the same network
- Access from the host to the containers via their IPs and ports

To inspect the network:

```bash
docker network inspect holly_network
```

To list all running containers with their IPs:

```bash
docker ps --format "{{.ID}}\t{{.Names}}" | xargs -I {} sh -c 'docker inspect -f "{{.Name}}: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" {}'
```
