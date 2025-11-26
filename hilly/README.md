# Hilly Container

This container provides a VNC server with Ubuntu and Xfce desktop environment.

## build notes
run 
build_kasm.sh 
this will build the hilly image
you may need to add:

git submodule add git@github.com:lingster/aiagents.git

To ensure that the aiagent code is cloned into the image.


## Features

- Ubuntu 22.04 with Xfce4 desktop environment
- TightVNC server for remote desktop access
- noVNC for browser-based VNC access

## Usage

### Starting the Container

```bash
docker-compose up -d
```

### Accessing the Desktop

1. **Using a VNC client:**
   - Connect to: `localhost:5901`
   - Password: `vncpassword` (default, can be changed in docker-compose.yml)

2. **Using noVNC (browser):**
   - Open: http://localhost:6080/vnc.html
   - Password: `vncpassword`

## Configuration

You can configure the following environment variables in the docker-compose.yml:

- `USER`: The username for the VNC user (default: vncuser)
- `PASSWORD`: The password for VNC access (default: vncpassword)
- `RESOLUTION`: The screen resolution (default: 1920x1080)

## Project Structure

```
hilly/
├── config/
│   └── supervisord.conf     # Supervisor configuration
├── data/                    # Persistent data volume
├── scripts/
│   ├── container/           # Scripts used inside the container
│   │   ├── create-shortcuts.sh        # Creates desktop shortcuts
│   │   └── entrypoint.sh 
│   │
│   ├── setup-vnc.sh         # Sets up VNC environment
│   └── ubuntu-install.sh    # Claude Desktop installer for Ubuntu
│
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## Troubleshooting

If you encounter issues with the VNC server:

1. Check supervisor logs:
   ```bash
   docker exec ubuntu-desktop-claude cat /var/log/supervisor/vncserver.log
   docker exec ubuntu-desktop-claude cat /var/log/supervisor/vncserver-err.log
   ```

2. Restart the VNC server:
   ```bash
   docker exec -u vncuser -it ubuntu-desktop-claude vncserver -kill :1
   docker exec -u vncuser -it ubuntu-desktop-claude vncserver :1
   ```

3. Restart the container:
   ```bash
   docker-compose restart
   ```

