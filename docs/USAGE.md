# CVE Tracker — Detailed Usage

## File Locations

Runtime files live in `~/.local/share/cve-tracker/` (not Desktop) because
macOS launchd cannot access `~/Desktop` without Full Disk Access permission.

### Runtime (used by launchd)

| File | Purpose |
|------|---------|
| `~/.local/share/cve-tracker/config.json` | User configuration (CVE IDs, schedule) |
| `~/.local/share/cve-tracker/state.json` | Last known CVE states + timestamps |
| `~/.local/share/cve-tracker/tracker.log` | Human-readable log of all checks |
| `~/.local/share/cve-tracker/.venv/` | Python venv with dependencies |
| `~/.local/share/cve-tracker/start.command` | Double-click launcher for manual start |
| `~/.local/share/cve-tracker/launchd_stdout.log` | launchd stdout |
| `~/.local/share/cve-tracker/launchd_stderr.log` | launchd stderr |

### launchd

| File | Purpose |
|------|---------|
| `~/Library/LaunchAgents/com.cve-tracker.plist` | launchd job definition |

Key plist settings:
- `RunAtLoad: true` — starts when you log in
- `KeepAlive: true` — restarts if killed/crashed
- `ProcessType: Interactive` — GUI process priority
- `ThrottleInterval: 10` — max 1 restart per 10 seconds

## API Details

- **Endpoint:** `https://cveawg.mitre.org/api/cve-id/{CVE-ID}`
- **Method:** GET (no auth required)
- **Response:** `{"cve_id": "CVE-2026-78840", "state": "RESERVED", ...}`
- **States:** `RESERVED` -> `PUBLISHED` (or `REJECTED`)
- **Rate:** 2 requests per run x 2 runs per day = 4 requests/day
- **Timeout:** 30 seconds per request

## Maintenance Commands

```bash
# --- Status ---
# Check if launchd job is loaded and running
launchctl list | grep cve-tracker

# Check if process exists
pgrep -fl cve_tracker

# View recent check log
tail -20 ~/.local/share/cve-tracker/tracker.log

# View saved state
cat ~/.local/share/cve-tracker/state.json

# --- Restart ---
# Kill app (launchd will auto-restart it)
pkill -f cve_tracker.menubar

# Or full reload:
launchctl remove com.cve-tracker
launchctl load ~/Library/LaunchAgents/com.cve-tracker.plist

# --- Manual check (CLI, no menu bar) ---
cve-check

# --- Manual start (if launchd not working) ---
# Double-click in Finder:
open ~/.local/share/cve-tracker/start.command
# Or run directly:
~/.local/share/cve-tracker/.venv/bin/python3 -m cve_tracker.menubar &

# --- Stop completely ---
launchctl remove com.cve-tracker

# --- Remove everything ---
./scripts/uninstall.sh
```

## Troubleshooting

### Menu bar icon not showing?
1. Check launchd: `launchctl list | grep cve-tracker`
2. Check errors: `cat ~/.local/share/cve-tracker/launchd_stderr.log`
3. Try manual run: `~/.local/share/cve-tracker/.venv/bin/python3 -m cve_tracker.menubar`
4. If macOS blocks: System Settings > Privacy & Security > Open Anyway

### No notifications when status changes?
1. System Settings > Notifications > Python -> make sure "Allow Notifications" is ON
2. Check log: `grep PUBLISHED ~/.local/share/cve-tracker/tracker.log`

### "Recheck Now" does nothing?
- Already checking (spinner should be showing)
- Network error — check log: `tail -5 ~/.local/share/cve-tracker/tracker.log`

### App not auto-starting after reboot?
1. Verify plist: `plutil -lint ~/Library/LaunchAgents/com.cve-tracker.plist`
2. Reload: `launchctl load ~/Library/LaunchAgents/com.cve-tracker.plist`
3. Check if another instance is blocking: `pgrep -fl cve_tracker`

### Two menu bar icons?
- One is from launchd, one from manual `start.command` — click Quit on one of them
- Only the launchd one will auto-restart

## When Both CVEs Are Published

Title changes to **CVE-PP**. You'll get 2 macOS notifications (one per CVE).

To stop tracking:
```bash
./scripts/uninstall.sh
```

## Technical Notes

- **Why not Desktop?** macOS sandboxing prevents launchd agents from reading
  files in `~/Desktop` without Full Disk Access. `~/.local/share/` avoids this.
- **Why rumps?** Lightweight Python library for macOS menu bar apps. Uses
  PyObjC (AppKit/NSStatusBar) under the hood.
- **Why not Unicode icons?** rumps 0.4.0 on Python 3.9 has issues rendering
  some Unicode characters in the menu bar. ASCII text titles work reliably.
- **Line endings matter:** `.command` files must have Unix line endings (LF).
