#!/bin/bash

# Ollama Chat UI Uninstaller
# This script removes the Ollama Chat UI from the system

set -e

INSTALL_DIR="/usr/local/share/ollama-chat"
BIN_DIR="/usr/local/bin"

echo "Ollama Chat UI Uninstaller"
echo "=========================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Check if installed
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Ollama Chat UI does not appear to be installed at $INSTALL_DIR"
  exit 1
fi

# Remove symlink
echo "Removing symlink..."
if [ -L "$BIN_DIR/ollama-chat" ]; then
  rm "$BIN_DIR/ollama-chat"
fi

# Remove installation directory
echo "Removing installation directory..."
rm -rf "$INSTALL_DIR"

echo
echo "Uninstallation complete!"
echo "Ollama Chat UI has been removed from your system."