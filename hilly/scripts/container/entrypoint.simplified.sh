#!/bin/bash
# Run VNC setup script
/usr/local/bin/setup-vnc.sh

# Fix electron permissions
/usr/local/bin/fix-electron-permissions.sh

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
