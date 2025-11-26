FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
	build-essential python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    #UV_NO_CACHE=1 \
    #UV_PLATFORM=linux \
    HOME=/app \
    PATH="/bin:/app/.local/bin:$PATH"

# Copy requirements files
COPY pyproject.toml uv.lock ./

# Create and activate a virtual environment, then install dependencies
#RUN /root/.cargo/bin/uv venv /app/.venv && \
#    . /app/.venv/bin/activate && \
#    /root/.cargo/bin/uv pip install -e .

# Copy the rest of the application
COPY . .

# Set the PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8090
RUN uv sync

ENV SHELLTOOLS_DIR=/app/aiagents
ENV BASE_URL=http://10.13.1.11:11434/v1
ENV API_KEY=sk_sglang_8bH7pQd2fWzX9yEaRkLpM3vN5xGtCuBvJ4wAsZxDcVfGgHjJkLmnOpQrStUvWxYz
ENV MODEL=openai/qwen3:32b

WORKDIR /data

# Command to run the application
CMD ["uv", "run", "fastapi", "run", "/app/rest_mcp_client/main.py", "--port", "8090"]
#CMD ["python", "main.py"]
