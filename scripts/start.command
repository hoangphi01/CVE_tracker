#!/bin/bash
# Double-click this file in Finder to launch CVE Tracker manually.
DATA_DIR="$HOME/.local/share/cve-tracker"
pkill -f "cve_tracker.menubar" 2>/dev/null
sleep 1
"$DATA_DIR/.venv/bin/python3" -m cve_tracker.menubar &
echo "Started CVE Tracker (PID: $!)"
sleep 2
