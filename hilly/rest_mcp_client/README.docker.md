# Docker Setup for REST MCP Client

This document explains how to run the REST MCP Client using Docker.

## Prerequisites

- Docker
- Docker Compose (optional, but recommended)

## Environment Variables

Before running the application, make sure to set the following environment variables or provide them in a `.env` file:

- `GOOGLE_API_KEY`: Required for Google LLM integration
- Any other environment variables needed by your specific deployment

## Running with Docker Compose

The easiest way to run the application is with Docker Compose:

```bash
# Build and start the container
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop the container
docker-compose down
```

## Running with Docker directly

If you prefer to use Docker commands directly:

```bash
# Build the Docker image
docker build -t rest-mcp-client .

# Run the container
docker run -p 8002:8002 -e GOOGLE_API_KEY=your_api_key rest-mcp-client
```

## Accessing the API

Once the container is running, you can access:

- API endpoint: http://localhost:8002/
- API documentation: http://localhost:8002/api/docs
- ReDoc documentation: http://localhost:8002/api/redoc

## Development with Docker

For development purposes, you might want to mount your local directory to see code changes without rebuilding:

```bash
docker run -p 8002:8002 -v $(pwd):/app -e GOOGLE_API_KEY=your_api_key rest-mcp-client
```
