#!/bin/bash
set -e

# Start the original KasmVNC entrypoint in the background
/dockerstartup/kasm_default_profile.sh "/dockerstartup/vnc_startup.sh" "/dockerstartup/kasm_startup.sh" --tail-log &

# Wait a bit for VNC to start
sleep 5

# Start supervisord for our API services
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
