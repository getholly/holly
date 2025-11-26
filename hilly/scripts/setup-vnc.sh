#!/bin/bash
set -e

# Initialize VNC environment for the user
USER=${USER:-vncuser}
HOME_DIR=/home/${USER}
VNC_DIR=${HOME_DIR}/.vnc
PASSWORD=${PASSWORD:-vncpassword}
RESOLUTION=${RESOLUTION:-1920x1080}

# Create necessary directories with proper permissions
mkdir -p ${VNC_DIR}
mkdir -p /var/log/supervisor

# Set VNC password
echo "${PASSWORD}" | vncpasswd -f > ${VNC_DIR}/passwd
chmod 600 ${VNC_DIR}/passwd
chown -R ${USER}:${USER} ${HOME_DIR}/.vnc

# Create VNC xstartup script
cat > ${VNC_DIR}/xstartup << EOF
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
startxfce4 &
EOF

# Set executable permissions
chmod +x ${VNC_DIR}/xstartup
chown ${USER}:${USER} ${VNC_DIR}/xstartup

# Ensure the user's home directory has the right ownership
chown -R ${USER}:${USER} ${HOME_DIR}

# Set correct permissions for the electron sandbox
ELECTRON_PATH=$(npm root -g)/electron
if [ -d "${ELECTRON_PATH}" ]; then
  SANDBOX_PATH="${ELECTRON_PATH}/dist/chrome-sandbox"
  if [ -f "${SANDBOX_PATH}" ]; then
    chown root:root "${SANDBOX_PATH}"
    chmod 4755 "${SANDBOX_PATH}"
  fi
fi

# Check if an existing VNC server is running and kill it if so
if [ -f ${VNC_DIR}/pid ]; then
  echo "Found existing VNC server process, killing it..."
  pkill -f "Xtightvnc :1" || true
  rm -f ${VNC_DIR}/pid ${VNC_DIR}/*.log
fi

echo "VNC environment setup completed successfully."
