#!/bin/zsh
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Status Report Generator - Installation Setup      ║${NC}"
echo -e "${BLUE}║  macOS with Local Ollama LLM                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ───────────────────────────────────────────────────────────────────
# Step 1: Check for Homebrew
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6]${NC} Checking Homebrew..."
if ! command -v brew &>/dev/null; then
    echo -e "${YELLOW}    Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo -e "${GREEN}    ✓ Homebrew ready${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 2: Install Ollama
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/6]${NC} Setting up Ollama..."
if command -v ollama &>/dev/null; then
    echo -e "${GREEN}    ✓ Ollama already installed${NC}"
else
    echo -e "${YELLOW}    Installing Ollama via Homebrew...${NC}"
    brew install ollama
fi
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 3: Pull the llama3.2 model
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/6]${NC} Downloading llama3.2 model..."
echo -e "    ${BLUE}(This may take 2-5 minutes on first run)${NC}"
ollama pull llama3.2
echo -e "${GREEN}    ✓ Model ready${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 4: Set up Ollama background service
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/6]${NC} Setting up Ollama background service..."
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.ollama.service.plist"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ollama.err</string>
</dict>
</plist>
PLIST

launchctl load "$PLIST_FILE" 2>/dev/null || launchctl unload "$PLIST_FILE" 2>/dev/null && launchctl load "$PLIST_FILE" 2>/dev/null || true
sleep 2
echo -e "${GREEN}    ✓ Ollama service configured${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 5: Install Python dependencies
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/6]${NC} Installing Python dependencies..."
python3 -m pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null || python3 -m pip install -r requirements.txt --break-system-packages
echo -e "${GREEN}    ✓ Dependencies installed${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────
# Step 6: Build the macOS app
# ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[6/6]${NC} Building macOS application..."
chmod +x build_macos_executable.sh
./build_macos_executable.sh > /dev/null 2>&1
echo -e "${GREEN}    ✓ Application built${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────
# Installation complete
# ───────────────────────────────────────────────────────────────────
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ✓ Installation Complete!                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

APP_PATH="$SCRIPT_DIR/dist/status-report-form.app"
if [ -d "$APP_PATH" ]; then
    echo -e "${GREEN}Application location:${NC}"
    echo "  $APP_PATH"
    echo ""
    echo -e "${GREEN}Quick launch:${NC}"
    echo "  open \"$APP_PATH\""
    echo ""
    echo -e "${GREEN}Or double-click from Finder:${NC}"
    echo "  Finder → Status report folder → dist → status-report-form.app"
    echo ""

    # Ask to install to Applications folder
    read -p "Would you like to copy the app to your Applications folder? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r "$APP_PATH" "$HOME/Applications/status-report-form.app" 2>/dev/null || \
        sudo cp -r "$APP_PATH" "/Applications/status-report-form.app"
        echo -e "${GREEN}✓ App installed to Applications folder${NC}"
        echo "  You can now launch it from Spotlight (Cmd+Space)"
    fi
fi

echo ""
echo -e "${YELLOW}Setup Notes:${NC}"
echo "  • Ollama will start automatically on next login"
echo "  • To start Ollama now: brew services start ollama"
echo "  • To stop Ollama: brew services stop ollama"
echo "  • To view Ollama logs: tail -f /tmp/ollama.log"
echo ""
echo -e "${GREEN}Ready to use! 🚀${NC}"

