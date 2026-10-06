#!/bin/bash
# Install CVE Tracker to ~/.local/share/cve-tracker/
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$HOME/.local/share/cve-tracker"
PLIST_SRC="$REPO_DIR/launchd/com.cve-tracker.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/com.cve-tracker.plist"

echo "Installing CVE Tracker..."

# Create data directory
mkdir -p "$DATA_DIR"

# Create venv if missing
if [ ! -d "$DATA_DIR/.venv" ]; then
    echo "Creating Python venv..."
    python3 -m venv "$DATA_DIR/.venv"
fi

# Install dependencies
echo "Installing dependencies..."
"$DATA_DIR/.venv/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"
"$DATA_DIR/.venv/bin/pip" install --quiet -e "$REPO_DIR"

# Copy config if not already present
if [ ! -f "$DATA_DIR/config.json" ]; then
    cp "$REPO_DIR/config.json" "$DATA_DIR/config.json"
    echo "Copied config.json to $DATA_DIR/"
fi

# Copy start.command
cp "$REPO_DIR/scripts/start.command" "$DATA_DIR/start.command"
chmod +x "$DATA_DIR/start.command"

# Install launchd plist
VENV_PYTHON="$DATA_DIR/.venv/bin/python3"
if [ -f "$PLIST_SRC" ]; then
    # Unload existing job if present
    launchctl remove com.cve-tracker 2>/dev/null || true

    sed -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
        -e "s|__DATA_DIR__|$DATA_DIR|g" \
        -e "s|__USER__|$USER|g" \
        "$PLIST_SRC" > "$PLIST_DST"

    echo "Installed launchd plist to $PLIST_DST"
    launchctl load "$PLIST_DST"
    echo "Loaded launchd job."
fi

echo ""
echo "Done! CVE Tracker is running in your menu bar."
echo "Data directory: $DATA_DIR"
echo "Config: $DATA_DIR/config.json"
