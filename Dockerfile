FROM python:3.11-slim

LABEL BUILD_ID="$(date +%s)"


# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    #UV_NO_CACHE=1 \
    #UV_PLATFORM=linux \
    HOME=/app \
    PATH="/app/.local/bin:$PATH"


# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    curl \
    libmagic-dev \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install NVM
#WORKDIR /app/.nvm
#WORKDIR /app
ENV HOME=/app
ENV NVM_DIR=/app/.nvm
ENV NODE_VERSION=22.14.0

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && \
    . $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default

# Add NVM to PATH
ENV PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH
ENV TMPDIR=/tmp

# Verify installation
RUN node --version && \
    npm --version

# Setup shell for proper NVM usage
RUN echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.bashrc


# Copy project files
COPY . /app/

# Install dependencies using uv
RUN uv sync

# Run the application
CMD ["./scripts/run_server.sh"]
