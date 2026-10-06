#!/bin/bash
# Remove CVE Tracker completely
set -e

DATA_DIR="$HOME/.local/share/cve-tracker"
PLIST="$HOME/Library/LaunchAgents/com.cve-tracker.plist"

echo "Uninstalling CVE Tracker..."

# Stop launchd job
launchctl remove com.cve-tracker 2>/dev/null || true

# Kill any running process
pkill -f "cve_tracker.menubar" 2>/dev/null || true
pkill -f "cve_menubar" 2>/dev/null || true

# Remove plist
if [ -f "$PLIST" ]; then
    rm "$PLIST"
    echo "Removed $PLIST"
fi

# Ask before removing data
if [ -d "$DATA_DIR" ]; then
    read -p "Remove data directory ($DATA_DIR)? [y/N] " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "$DATA_DIR"
        echo "Removed $DATA_DIR"
    else
        echo "Kept $DATA_DIR (state.json and logs preserved)"
    fi
fi

echo "Done."
