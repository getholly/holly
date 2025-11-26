#!/bin/bash
cd /home/$USER/claude-install
./ubuntu-install.sh
echo "Claude Desktop installed successfully"

# Create autostart directory if it doesn't exist
mkdir -p /home/$USER/.config/autostart

# Create autostart entry for Claude Desktop
echo "[Desktop Entry]
Type=Application
Exec=bash -c \"sleep 5 && electron /home/$USER/.local/lib/claude-desktop/app.asar --start-fullscreen\"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Claude Desktop Autostart
Comment=Start Claude Desktop in fullscreen mode" > /home/$USER/.config/autostart/claude-desktop.desktop

# Set correct permissions
chmod +x /home/$USER/.config/autostart/claude-desktop.desktop

# Create a fullscreen toggle script
echo "#!/bin/bash
wmctrl -r \"Claude\" -b toggle,fullscreen" > /home/$USER/toggle-fullscreen.sh
chmod +x /home/$USER/toggle-fullscreen.sh

echo "Claude Desktop will now start automatically in fullscreen mode when you log in"
