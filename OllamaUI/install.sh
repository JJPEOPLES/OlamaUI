#!/bin/bash

# Ollama Chat UI Installer
# This script installs the Ollama Chat UI and makes it available system-wide

set -e

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/share/ollama-chat"
BIN_DIR="/usr/local/bin"

echo "Ollama Chat UI Installer"
echo "========================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
  echo "Warning: Ollama does not appear to be installed."
  echo "You can install it from https://ollama.com/download"
  echo
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "Copying files..."
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# Make scripts executable
echo "Setting permissions..."
chmod +x "$INSTALL_DIR/ollama-chat"
chmod +x "$INSTALL_DIR/terminal_app/ollama_chat.py"
chmod +x "$INSTALL_DIR/gui_app/ollama_gui.py"

# Create symlink
echo "Creating symlink..."
ln -sf "$INSTALL_DIR/ollama-chat" "$BIN_DIR/ollama-chat"

# Install dependencies
echo "Installing dependencies..."

# Python dependencies
if command -v pip3 &> /dev/null; then
  pip3 install requests python-dotenv

  # Check for tkinter
  if python3 -c "import tkinter" &> /dev/null; then
    echo "Tkinter is installed (required for GUI application)"
  else
    echo "Warning: Tkinter is not installed. GUI application will not work."
    echo "To install Tkinter:"
    echo "  - Debian/Ubuntu: sudo apt-get install python3-tk"
    echo "  - Fedora: sudo dnf install python3-tkinter"
    echo "  - Arch: sudo pacman -S tk"
    echo "  - macOS: Tkinter should be included with Python from python.org"
  fi
else
  echo "Warning: pip3 not found. Python dependencies not installed."
fi

# Ruby dependencies (optional)
if command -v bundle &> /dev/null; then
  cd "$INSTALL_DIR/ruby_app"
  bundle install
else
  echo "Note: Bundler not found. Ruby dependencies not installed."
  echo "To use the Ruby web UI, install Ruby and Bundler, then run:"
  echo "  cd $INSTALL_DIR/ruby_app && bundle install"
fi

# Create desktop entry for GUI application
echo "Creating desktop entry..."
cat > /usr/share/applications/ollama-chat.desktop << EOF
[Desktop Entry]
Name=Ollama Chat
Comment=Chat with Ollama AI models
Exec=ollama-chat --gui
Icon=$INSTALL_DIR/gui_app/icon.png
Terminal=false
Type=Application
Categories=Utility;AI;
Keywords=AI;Chat;Ollama;
EOF

echo
echo "Installation complete!"
echo "You can now run 'ollama-chat' from anywhere."
echo
echo "Usage examples:"
echo "  ollama-chat                   # Terminal UI"
echo "  ollama-chat --gui             # Graphical UI"
echo "  ollama-chat --web             # Python web UI"
echo "  ollama-chat --web --ruby      # Ruby web UI"
echo "  ollama-chat --model llama3    # Terminal UI with specific model"
echo
echo "The GUI application is also available in your application menu."
echo
echo "For more options, run: ollama-chat --help"