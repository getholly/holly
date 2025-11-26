#!/bin/bash
# Run VNC setup script
/usr/local/bin/setup-vnc.sh

# Fix electron permissions
/usr/local/bin/fix-electron-permissions.sh

su - vncuser -c '/usr/bin/vncserver :1 -geometry 1920x1080 -depth 24 -localhost'

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf


