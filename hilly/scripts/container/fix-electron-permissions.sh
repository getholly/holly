#!/bin/bash
ELECTRON_PATH=$(npm root -g)/electron
if [ -d "$ELECTRON_PATH" ]; then
  SANDBOX_PATH="$ELECTRON_PATH/dist/chrome-sandbox"
  if [ -f "$SANDBOX_PATH" ]; then
    sudo chown root:root "$SANDBOX_PATH"
    sudo chmod 4755 "$SANDBOX_PATH"
  fi
fi
