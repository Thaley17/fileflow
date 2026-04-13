#!/bin/bash
# ──────────────────────────────────────────────────
# FileFlow Installer
# Installs dependencies and adds `fileflow` to your PATH
# ──────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  FileFlow Installer"
echo "  ──────────────────"
echo ""

# 1. Check Python 3
if ! command -v python3 &>/dev/null; then
  echo "  ERROR: Python 3 is required but not installed."
  echo ""
  echo "  Install it:"
  echo "    macOS:  brew install python3"
  echo "    Ubuntu: sudo apt install python3 python3-pip"
  echo ""
  exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "  Found $PYTHON_VERSION"

# 2. Install Python dependencies
echo "  Installing Python packages..."
pip3 install -q flask markdown markupsafe 2>/dev/null || \
  pip3 install --user -q flask markdown markupsafe 2>/dev/null || {
    echo "  ERROR: Could not install Python packages."
    echo "  Try: pip3 install flask markdown markupsafe"
    exit 1
  }
echo "  Done."

# 3. Make scripts executable
chmod +x "$SCRIPT_DIR/fileflow"
chmod +x "$SCRIPT_DIR/start.sh"

# 4. Create symlink on PATH
LINK_CREATED=false
for DIR in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin" "$HOME/bin"; do
  if [ -d "$DIR" ] && [ -w "$DIR" ]; then
    ln -sf "$SCRIPT_DIR/fileflow" "$DIR/fileflow"
    echo "  Linked: $DIR/fileflow"
    LINK_CREATED=true
    break
  fi
done

if [ "$LINK_CREATED" = false ]; then
  # Create ~/.local/bin if nothing else worked
  mkdir -p "$HOME/.local/bin"
  ln -sf "$SCRIPT_DIR/fileflow" "$HOME/.local/bin/fileflow"
  echo "  Linked: $HOME/.local/bin/fileflow"
  echo ""
  echo "  NOTE: Add ~/.local/bin to your PATH if not already:"
  echo '    echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> ~/.zshrc'
  echo '    source ~/.zshrc'
fi

# 5. Create default folders
mkdir -p "$HOME/FileFlow/Inbox" "$HOME/FileFlow/Archive"

echo ""
echo "  Installation complete!"
echo ""
echo "  Quick start:"
echo "    fileflow          # start + open browser"
echo "    fileflow status   # check what's running"
echo "    fileflow stop     # shut it down"
echo "    fileflow help     # see all commands"
echo ""
echo "  Default folders created:"
echo "    ~/FileFlow/Inbox"
echo "    ~/FileFlow/Archive"
echo ""
echo "  Drop files in ~/FileFlow/Inbox and run 'fileflow' to start sorting."
echo ""
