#!/bin/bash

# Exit on error
set -e

# Build the Docker image
echo "Building Docker image..."
docker build -t rest-mcp-client .

# Run the container
echo "Running Docker container..."
docker run -p 8002:8002 \
  -e GOOGLE_API_KEY=${GOOGLE_API_KEY:-your_google_api_key} \
  --name rest-mcp-client \
  rest-mcp-client

# Cleanup on exit
trap 'docker stop rest-mcp-client && docker rm rest-mcp-client' EXIT
