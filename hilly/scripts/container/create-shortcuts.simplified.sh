#!/bin/bash
USER=${USER:-vncuser}

# Create desktop directory if it doesn't exist
mkdir -p /home/$USER/Desktop

# Create fullscreen toggle shortcut on desktop
echo '[Desktop Entry]
Name=Toggle Claude Fullscreen
Comment=Toggle fullscreen mode for Claude Desktop
Exec=/home/'$USER'/toggle-fullscreen.sh
Terminal=false
Type=Application
Icon=view-fullscreen
' > /home/$USER/Desktop/toggle-claude-fullscreen.desktop
chmod +x /home/$USER/Desktop/toggle-claude-fullscreen.desktop
chown $USER:$USER /home/$USER/Desktop/toggle-claude-fullscreen.desktop

# Create a readme file on the desktop
echo "# Claude Desktop VNC Container

Claude Desktop is pre-installed and configured to start automatically when you log in.

## Keyboard Shortcuts

- **Toggle Fullscreen**: Use the desktop shortcut or press F11
- **Copy**: Ctrl+C
- **Paste**: Ctrl+V

## Need Help?

If you encounter any issues with Claude Desktop, please check the documentation or reach out to the container maintainer.
" > /home/$USER/Desktop/README.md
chown $USER:$USER /home/$USER/Desktop/README.md
