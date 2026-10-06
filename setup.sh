#!/bin/bash
# CVE Tracker — Install / Uninstall / Restart
# Usage:  ./setup.sh install | uninstall | restart

set -euo pipefail

INSTALL_DIR="$HOME/.local/share/cve-tracker"
PLIST_NAME="com.hoangphi.cve-tracker"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$INSTALL_DIR/.venv"

usage() {
    echo "Usage: $0 {install|uninstall|restart}"
    echo ""
    echo "  install    Create venv, deploy files, register launchd service"
    echo "  uninstall  Stop service, remove launchd plist and install directory"
    echo "  restart    Stop and restart the running menu bar app"
    exit 1
}

do_install() {
    echo "==> Installing CVE Tracker..."

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Create/update venv
    if [ ! -d "$VENV_DIR" ]; then
        echo "    Creating Python venv..."
        python3 -m venv "$VENV_DIR"
    fi

    echo "    Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

    # Deploy app file
    echo "    Deploying cve_menubar.py..."
    cp "$SCRIPT_DIR/cve_tracker/../cve_menubar.py" "$INSTALL_DIR/cve_menubar.py" 2>/dev/null \
        || cp "$SCRIPT_DIR/cve_menubar.py" "$INSTALL_DIR/cve_menubar.py" 2>/dev/null \
        || {
            # Fallback: use the runtime file if source isn't found at repo root
            if [ -f "$INSTALL_DIR/cve_menubar.py" ]; then
                echo "    (cve_menubar.py already in place)"
            else
                echo "    ERROR: cve_menubar.py not found in source tree"
                exit 1
            fi
        }

    # Deploy CLI checker if it exists
    [ -f "$SCRIPT_DIR/cve_tracker.py" ] && cp "$SCRIPT_DIR/cve_tracker.py" "$INSTALL_DIR/cve_tracker.py"

    # Write launchd plist
    echo "    Writing launchd plist..."
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/python3</string>
        <string>$INSTALL_DIR/cve_menubar.py</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ProcessType</key>
    <string>Interactive</string>

    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/launchd_stderr.log</string>

    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
PLIST

    # Load and start
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    echo "    Service loaded and started."

    echo ""
    echo "==> Installed successfully!"
    echo "    App dir:  $INSTALL_DIR"
    echo "    Plist:    $PLIST_PATH"
    echo "    The menu bar icon should appear shortly."
}

do_uninstall() {
    echo "==> Uninstalling CVE Tracker..."

    # Stop and unload launchd service
    if [ -f "$PLIST_PATH" ]; then
        echo "    Stopping service..."
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        rm -f "$PLIST_PATH"
        echo "    Removed launchd plist."
    fi

    # Kill any lingering process
    pkill -f cve_menubar.py 2>/dev/null || true

    # Remove install directory
    if [ -d "$INSTALL_DIR" ]; then
        echo "    Removing $INSTALL_DIR..."
        rm -rf "$INSTALL_DIR"
    fi

    echo ""
    echo "==> Uninstalled. All files removed."
}

do_restart() {
    echo "==> Restarting CVE Tracker..."
    if [ -f "$PLIST_PATH" ]; then
        launchctl stop "$PLIST_NAME" 2>/dev/null || true
        sleep 1
        launchctl start "$PLIST_NAME" 2>/dev/null || true
        echo "    Restarted via launchd."
    else
        echo "    No launchd plist found. Run '$0 install' first."
        exit 1
    fi
}

case "${1:-}" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
    restart)   do_restart ;;
    *)         usage ;;
esac
