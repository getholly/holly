# see: https://kasmweb.com/docs/latest/how_to/building_images.html
# ============================================
# Stage 1: Builder - Install dependencies and build artifacts
# ============================================
FROM kasmweb/ubuntu-noble-dind:1.17.0 AS builder

USER root

ENV HOME=/home/kasm-default-profile
ENV STARTUPDIR=/dockerstartup
ENV INST_SCRIPTS=$STARTUPDIR/install
WORKDIR $HOME

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC

# Base system packages (stable, rarely change - cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    git \
    ca-certificates \
    apt-transport-https \
    gnupg \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Development and build tools (may change more frequently)
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    build-essential \
    patch \
    supervisor \
    golang-go \
    hugo \
    weasyprint \
    libmagic1 libmagic-dev \
    p7zip-full icoutils imagemagick \
    xdotool mousetrap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get update && \
    apt-get install -y git-lfs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=$PATH:/usr/local/go/bin

# Disable pm-utils/warnings
RUN touch /usr/bin/pm-is-supported && chmod +x /usr/bin/pm-is-supported

# Create non-root user directories
ARG USERNAME=kasm-user
ARG USER_UID=1000
ARG USER_GID=1000

RUN mkdir -p /app/data && \
    chown -R $USER_UID:$USER_GID /app && \
    chown -R $USER_UID:$USER_GID /home/$USERNAME

# Install NVM and Node
ENV NVM_DIR=$HOME/.nvm
ENV NODE_VERSION=23.11.0

# Copy uv from official image (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && \
    . $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default && \
    npm install -g tree-sitter-cli

ENV PATH=$PATH:$NVM_DIR/versions/node/v$NODE_VERSION/bin
ENV TMPDIR=/tmp

# Verify node installation
RUN node --version && npm --version

# Setup shell for proper NVM usage
RUN echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.bashrc

# Initialize git-lfs
RUN git lfs install

ENV PATH=$PATH:$HOME/.local/bin

# Copy and install Python dependencies
WORKDIR /app/aiagents
COPY --chown=$USER_UID:$USER_GID aiagents /app/aiagents/
RUN uv sync

WORKDIR /app/rest_mcp_client
COPY --chown=$USER_UID:$USER_GID rest_mcp_client /app/rest_mcp_client/
RUN uv sync


# ============================================
# Stage 2: Runtime - Final optimized image
# ============================================
FROM kasmweb/ubuntu-noble-dind:1.17.0 AS runtime

# Add OpenContainers labels for better container metadata
LABEL org.opencontainers.image.description="AI Agent project container"
LABEL org.opencontainers.image.licenses="MIT"

USER root

ENV HOME=/home/kasm-default-profile
ENV STARTUPDIR=/dockerstartup
ENV INST_SCRIPTS=$STARTUPDIR/install
WORKDIR $HOME

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="$PATH:/home/kasm-user/.local/bin" \
    TZ=UTC

# Base system packages (stable, rarely change - cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    git \
    ca-certificates \
    apt-transport-https \
    gnupg \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Development and runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    build-essential \
    patch \
    supervisor \
    golang-go \
    hugo \
    weasyprint \
    libmagic1 libmagic-dev \
    p7zip-full icoutils imagemagick \
    xdotool mousetrap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get update && \
    apt-get install -y git-lfs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=$PATH:/usr/local/go/bin

# Disable pm-utils/warnings
RUN touch /usr/bin/pm-is-supported && chmod +x /usr/bin/pm-is-supported

# User configuration
ARG USERNAME=kasm-user
ARG USER_UID=1000
ARG USER_GID=1000

# NVM and Node environment
ENV NVM_DIR=$HOME/.nvm
ENV NODE_VERSION=23.11.0
ENV PATH=$PATH:$NVM_DIR/versions/node/v$NODE_VERSION/bin
ENV TMPDIR=/tmp
ENV PATH=$PATH:$HOME/.local/bin

# Copy uv binaries
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

# Copy NVM and Node from builder
COPY --from=builder $HOME/.nvm $HOME/.nvm

# Copy installed applications from builder
COPY --from=builder /app /app

# Setup shell for proper NVM usage
RUN echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.bashrc

# Initialize git-lfs
RUN git lfs install

# Expose ports
EXPOSE 8000
EXPOSE 8181
EXPOSE 8090

# Working directory for data
WORKDIR /data

# Setup git commits - can override when we spin up the container
ENV GIT_EMAIL=holly@github.me.uk
ENV GIT_USER="Holly AI Agent"
RUN git config --global user.email "${GIT_EMAIL}" && \
    git config --global user.name "${GIT_USER}"

WORKDIR $HOME

# Set ownership in a single layer
RUN mkdir -p /app/data /data && \
    chown -R $USER_UID:$USER_GID $HOME /app /data

# Copy startup scripts
COPY custom_startup.sh $STARTUPDIR

# VNC configuration
COPY kasm_configs/vnc_startup.sh /dockerstartup/
COPY kasm_configs/kasmvnc_defaults.yaml /usr/share/kasmvnc/kasmvnc_defaults.yaml

# Fix line endings (CRLF to LF) and set execute permissions for shell scripts
RUN sed -i 's/\r$//' /dockerstartup/vnc_startup.sh /dockerstartup/custom_startup.sh && \
    chmod +x /dockerstartup/vnc_startup.sh /dockerstartup/custom_startup.sh

RUN usermod -aG video $USERNAME && usermod -aG video root

ENV KASM_SVC_WEBCAM=0
ENV KASM_SVC_AUDIO_INPUT=0
ENV KASM_SVC_AUDIO=0
ENV KASM_SVC_GAMEPAD=0
ENV KASM_SVC_PRINTER=0

# Final permissions setup
RUN chown 1000:0 $HOME && \
    $STARTUPDIR/set_user_permission.sh $HOME && \
    mkdir -p $HOME && chown -R 1000:0 $HOME

USER 1000

# Runtime environment variables moved to docker-compose.yml for security:
# - SHELLTOOLS_DIR
# - BASE_URL
# - API_KEY (sensitive)
# - MODEL
