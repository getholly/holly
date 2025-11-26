# VNC Server Configuration Fixes

This document explains the fixes made to resolve VNC server startup issues in the Claude VNC container.

## Issues Identified

1. Supervisord warning about running as root without specifying the user
2. Supervisord warning about running without HTTP authentication
3. VNC server repeatedly failing to start with exit status 13 (permission denied)

## Changes Made

### 1. Updated Supervisord Configuration

The supervisord.conf file has been modified to:
- Explicitly set user=root in the supervisord section
- Add HTTP authentication for the unix_http_server
- Add proper logging configuration for VNC and noVNC services
- Specify startsecs and startretries to prevent immediate failure of services

### 2. Added VNC Setup Script

Created a new script `setup-vnc.sh` that:
- Properly sets up the VNC environment for the specified user
- Creates all necessary directories with correct permissions
- Ensures the VNC password file has the right permissions
- Creates a proper xstartup script for launching Xfce4
- Cleans up any existing VNC server processes
- Sets correct permissions for the electron sandbox

### 3. Modified Dockerfile

The Dockerfile has been updated to:
- Create log directories with proper permissions
- Add the VNC setup script and make it executable
- Create an entrypoint script that runs setup before starting supervisord
- Ensure all files have proper ownership and permissions

### 4. Updated Docker Compose File

The docker-compose.yml file has been modified to:
- Use the fixed Dockerfile
- Add privileged mode to ensure VNC has necessary permissions
- Mount supervisor logs for easier debugging

## How to Apply These Fixes

1. Replace the original configuration files with the fixed versions:
   ```bash
   cp config/supervisord.conf.fixed config/supervisord.conf
   cp Dockerfile.fixed Dockerfile
   cp docker-compose.yml.fixed docker-compose.yml
   ```

2. Rebuild and restart the container:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

## Debugging Suggestions

If issues persist after applying these fixes:

1. Check the supervisor logs:
   ```bash
   docker exec ubuntu-desktop-claude cat /var/log/supervisor/vncserver.log
   docker exec ubuntu-desktop-claude cat /var/log/supervisor/vncserver-err.log
   ```

2. Verify the VNC environment:
   ```bash
   docker exec ubuntu-desktop-claude ls -la /home/vncuser/.vnc/
   ```

3. Try running VNC server manually within the container:
   ```bash
   docker exec -u vncuser -it ubuntu-desktop-claude vncserver -kill :1
   docker exec -u vncuser -it ubuntu-desktop-claude vncserver :1
   ```
