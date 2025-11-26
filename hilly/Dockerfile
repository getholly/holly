# see: https://kasmweb.com/docs/latest/how_to/building_images.html
#FROM kasmweb/ubuntu-noble-desktop:1.17.0
FROM kasmweb/ubuntu-noble-dind:1.17.0
#FROM ubuntu:latest
# Set environment variables
USER root


ENV HOME=/home/kasm-default-profile
ENV STARTUPDIR=/dockerstartup
ENV INST_SCRIPTS=$STARTUPDIR/install
WORKDIR $HOME


######### Customize Container Here ###########
# See: https://kasmweb.com/docs/latest/how_to/building_images.html#custom-startup

# Add OpenContainers labels for better container metadata
#LABEL org.opencontainers.image.source="https://github.com/${GITHUB_REPOSITORY}"
LABEL org.opencontainers.image.description="AI Agent project container"
LABEL org.opencontainers.image.licenses="MIT"
#LABEL org.opencontainers.image.revision="${GITHUB_SHA}"
#LABEL org.opencontainers.image.version="${GITHUB_REF##*/}"


ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="$PATH:/home/kasm-user/.local/bin" \
    TZ=UTC

# for macos
#ARG USER_UID=502
#ARG USER_GID=20


# Install runtime dependencies (including ca-certificates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    git \
    vim \
    less \
    build-essential \
    patch \
    ca-certificates \
    supervisor \
    apt-transport-https \
    gnupg \
    golang-go \
    hugo \
    tzdata \
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
    # Clean up to reduce image size
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install hugo
ENV PATH=$PATH:/usr/local/go/bin

#RUN  go install github.com/jmooring/hvm@latest

# disable pm-utils/warnings:
RUN touch /usr/bin/pm-is-supported && \
    chmod +x /usr/bin/pm-is-supported

# Create non-root user
ARG USERNAME=kasm-user
ARG USER_UID=1000
ARG USER_GID=1000
#RUN groupadd --gid $USER_GID $USERNAME || \
    #(groupmod -g $USER_GID $USERNAME 2>/dev/null || true) && \
    #useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    #mkdir -p /app/data && \
    #chown -R $USER_UID:$USER_GID /app
RUN mkdir -p /app/data && \
    chown -R $USER_UID:$USER_GID /app && \
    chown -R $USER_UID:$USER_GID /home/$USERNAME

# User switch
#USER $USERNAME

# Install NVM
WORKDIR $HOME/.nvm
WORKDIR $HOME

ENV NVM_DIR=$HOME/.nvm
ENV NODE_VERSION=23.11.0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

RUN . $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default && \
    npm install -g tree-sitter-cli

# Add NVM to PATH
ENV PATH=$PATH:/bin:$NVM_DIR/versions/node/v$NODE_VERSION/bin
ENV TMPDIR=/tmp

# Verify installation
RUN node --version && \
    npm --version

# Setup shell for proper NVM usage
RUN echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.bashrc


# Initialize git-lfs
RUN git lfs install

# Install uv
ENV PATH=$PATH:$HOME/.local/bin

# Copy application files
WORKDIR /app/aiagents

COPY --chown=$USER_UID:$USER_GID aiagents /app/aiagents/
COPY --chown=$USER_UID:$USER_GID rest_mcp_client /app/rest_mcp_client/
#COPY --chown=$USER_UID:$USER_GID aiagent/pyproject.toml aiagent/remote_server.py /app/
#COPY --chown=$USER_UID:$USER_GID aiagent/remote_server_lib /app/remote_server_lib/

# Install Python dependencies
# incase of failure, have you run:
# git submodule init 
# git submodule update
RUN uv sync

WORKDIR /app/rest_mcp_client
RUN uv sync

# Install tree-sitter
#WORKDIR /app/.tree-sitter/grammars
#RUN git clone --depth=1 https://github.com/tree-sitter/tree-sitter-python && cd tree-sitter-python && tree-sitter generate
#RUN git clone --depth=1 https://github.com/tree-sitter/tree-sitter-javascript && cd tree-sitter-javascript && tree-sitter generate

# Expose port
EXPOSE 8000

# AI Agent api
EXPOSE 8181

# REST MCP client API
EXPOSE 8090

# Working directory for data
WORKDIR /data

# setup git commits - can override when we spin up the container
ENV GIT_EMAIL=holly@github.me.uk
ENV GIT_USER="Holly AI Agent"
RUN git config --global user.email "${GIT_EMAIL}"
RUN git config --global user.name "${GIT_USER}"

WORKDIR $HOME


# this could be used to navigate around code using LSP server
#git clone git@github.com:lingster/serena.git /app/serena

RUN chown -R $USER_UID:$USER_GID $HOME && \
    chown -R $USER_UID:$USER_GID /app && \
    chown -R $USER_UID:$USER_GID /data

COPY custom_startup.sh $STARTUPDIR

#COPY custom_startup.sh .
#RUN cat custom_startup.sh >> $STARTUPDIR/custom_startup.sh && chmod +x $STARTUPDIR/custom_startup.sh


# required for firecracker
#COPY --from=build /go/src/github.com/alexellis/firecracker-init-lab/init/init /init

# Use supervisor as the entrypoint
#COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-l", "/var/log/supervisord.log"]

# These are to remove the ssl password requirements for vnc
COPY kasm_configs/vnc_startup.sh /dockerstartup/
COPY kasm_configs/kasmvnc_defaults.yaml /usr/share/kasmvnc/kasmvnc_defaults.yaml

RUN usermod -aG video $USERNAME && usermod -aG video root
ENV KASM_SVC_WEBCAM=0
ENV KASM_SVC_AUDIO_INPUT=0
ENV KASM_SVC_AUDIO=0
ENV KASM_SVC_GAMEPAD=0
ENV KASM_SVC_PRINTER=0

# Runtime environment variables moved to docker-compose.yml for security:
# - SHELLTOOLS_DIR
# - BASE_URL
# - API_KEY (sensitive)
# - MODEL

######### End Customizations ###########


RUN chown 1000:0 $HOME
RUN $STARTUPDIR/set_user_permission.sh $HOME

ENV HOME=/home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

USER 1000


