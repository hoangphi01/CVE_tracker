# CVE Status Tracker — Menu Bar App

Persistent macOS menu bar app that tracks the publication status of:
- **CVE-2026-78840** — Privilege escalation via XHR endpoints, JS framework, CDN
- **CVE-2026-78841** — IDOR via unauthenticated CAN.db/config/xửLý API

Both CVEs were assigned by MITRE on 2026-09-11 for vulnerabilities in
I&E Vietnam "Connections" SaaS Platform (hanu.connections.vn).

MITRE tracking ID: `{CMI: MCID15948087}`

---

## Menu Bar Title Codes

The menu bar shows a short code with one letter per tracked CVE:

| Letter | Meaning |
|--------|---------|
| **R** | RESERVED (waiting) |
| **P** | PUBLISHED |
| **?** | Unknown / error |

Examples: `CVE-RR` (2 reserved), `CVE-RRR` (3 reserved), `CVE-PP` (2 published), `CVE-RRRRR` (5 reserved — maximum).

During a check, the title shows a spinner: `CVE /` → `CVE -` → `CVE \` → `CVE |`

## Menu Dropdown

Click the title to see the dropdown:

```
CVE-2026-78840: RESERVED      ← click opens cve.org page
CVE-2026-78841: RESERVED      ← click opens cve.org page
─────────────────────────
Last: 13:26 17/09              ← last check timestamp
─────────────────────────
Recheck Now                    ← manual check button
[CVE-XXXX-XXXXX  Enter]        ← inline lookup text field
  CVE-2024-1234: PUBLISHED     ← lookup result
─────────────────────────
Settings                       ← submenu
  Add CVE...                   ← dialog to add a new CVE (max 5)
  ─────────────────────
  CVE-2026-78840  ✕            ← click to remove
  CVE-2026-78841  ✕            ← click to remove
─────────────────────────
Quit
```

## Features

- **Settings menu** — add/remove tracked CVEs at runtime (max 5); changes persist to `config.json`
- **Smart CVE input** — auto-prepends `CVE-` and inserts dash after year (e.g. `2026778866` → `CVE-2026-778866`)
- **Auto-check** at 9:03 and 15:03 local time (CEST) daily
- **Manual check** via "Recheck Now" in dropdown
- **Lookup any CVE** — inline text field in the menu; type a CVE ID and press Enter.
  Accepts flexible input: `CVE-2024-1234`, `2024-1234`, or just `20241234` (auto-adds `CVE-` prefix and dash after year)
- **macOS notification** with sound when status changes (RESERVED → PUBLISHED)
- **Auto-start at login** via launchd (`RunAtLoad`)
- **Auto-restart on crash** via launchd (`KeepAlive`)
- **Survives sleep/wake** — launchd keeps the process alive
- **Safe API usage** — only 2 requests per check, 3s delay, custom User-Agent
- Click any CVE line → opens its page on cve.org in browser

## API Details

- **Endpoint:** `https://cveawg.mitre.org/api/cve-id/{CVE-ID}`
- **Method:** GET (no auth required)
- **Response:** `{"cve_id": "CVE-2026-78840", "state": "RESERVED", ...}`
- **States:** `RESERVED` → `PUBLISHED` (or `REJECTED`)
- **Rate:** 2 requests per run × 2 runs per day = 4 requests/day (well within limits)
- **User-Agent:** `CVE-Tracker/1.0 (personal; 2-requests-per-day)`
- **Timeout:** 30 seconds per request

---

## File Locations

Runtime files live in `~/.local/share/cve-tracker/` (not Desktop) because
macOS launchd cannot access `~/Desktop` without Full Disk Access permission.

### Runtime (used by launchd)

| File | Purpose |
|------|---------|
| `~/.local/share/cve-tracker/cve_menubar.py` | Menu bar app (main, runs persistently) |
| `~/.local/share/cve-tracker/cve_tracker.py` | Standalone CLI checker (independent) |
| `~/.local/share/cve-tracker/.venv/` | Python 3.9 venv with `rumps` 0.4.0, `pyobjc-core` 12.0, `pyobjc-framework-Cocoa` 12.0 |
| `~/.local/share/cve-tracker/config.json` | Persisted CVE list + settings (created on first Add/Remove) |
| `~/.local/share/cve-tracker/state.json` | Last known CVE states + timestamps |
| `~/.local/share/cve-tracker/tracker.log` | Human-readable log of all checks |
| `~/.local/share/cve-tracker/start.command` | Double-click launcher (for manual start) |
| `~/.local/share/cve-tracker/launchd_stdout.log` | launchd stdout |
| `~/.local/share/cve-tracker/launchd_stderr.log` | launchd stderr |

### launchd

| File | Purpose |
|------|---------|
| `~/Library/LaunchAgents/com.hoangphi.cve-tracker.plist` | launchd job definition |

Key plist settings:
- `RunAtLoad: true` — starts when you log in
- `KeepAlive: true` — restarts if killed/crashed
- `ProcessType: Interactive` — GUI process priority
- `ThrottleInterval: 10` — max 1 restart per 10 seconds

### Backup / source (in project folder)

| File | Purpose |
|------|---------|
| `~/Desktop/1_CVE_HANU/Tracking/cve_menubar.py` | Source backup of menu bar app |
| `~/Desktop/1_CVE_HANU/Tracking/cve_tracker.py` | Source backup of CLI checker |
| `~/Desktop/1_CVE_HANU/Tracking/requirements.txt` | Python dependencies |
| `~/Desktop/1_CVE_HANU/Tracking/setup.sh` | Install / uninstall / restart script |
| `~/Desktop/1_CVE_HANU/Tracking/DOCS.md` | This documentation |

---

## How It Works

1. **Login** → launchd starts `cve_menubar.py` automatically
2. App shows **"CVE-RR"** in menu bar (both RESERVED)
3. Every **60 seconds**, the app checks if current time is 9:03 or 15:03
4. When triggered (scheduled or "Recheck Now"):
   - Title shows spinner: `CVE /` → `CVE -` → `CVE \` → `CVE |`
   - Queries MITRE API for CVE-2026-78840 (waits for response)
   - Waits 3 seconds (polite delay)
   - Queries MITRE API for CVE-2026-78841 (waits for response)
   - Updates menu items, saves state to `state.json`, logs to `tracker.log`
   - If status changed → sends macOS notification with sound
   - Updates title code (e.g., `CVE-RR` → `CVE-PR`)
5. **Sleep/wake** → launchd keeps process alive, missed checks run when awake
6. **Crash** → launchd auto-restarts within 10 seconds

---

## Setup Script

`setup.sh` handles install, uninstall, and restart:

```bash
./setup.sh install     # Create venv, deploy files, register launchd service
./setup.sh restart     # Restart the running menu bar app
./setup.sh uninstall   # Stop service, remove launchd plist and all files
```

## Maintenance Commands

```bash
# ─── Status ─────────────────────────────────────────────
launchctl list | grep cve-tracker
pgrep -fl cve_menubar

# View recent check log
tail -20 ~/.local/share/cve-tracker/tracker.log

# View saved state / tracked CVEs
cat ~/.local/share/cve-tracker/state.json
cat ~/.local/share/cve-tracker/config.json

# ─── Quick restart (launchd auto-restarts) ──────────────
pkill -f cve_menubar.py

# ─── Manual check (CLI, no menu bar) ───────────────────
python3 ~/Desktop/1_CVE_HANU/Tracking/cve_tracker.py
```

---

## Troubleshooting

### Menu bar icon not showing?
1. Check launchd: `launchctl list | grep cve-tracker`
2. Check errors: `cat ~/.local/share/cve-tracker/launchd_stderr.log`
3. Try manual run: `~/.local/share/cve-tracker/.venv/bin/python3 ~/.local/share/cve-tracker/cve_menubar.py`
4. If macOS blocks: System Settings > Privacy & Security > Open Anyway

### No notifications when status changes?
1. System Settings > Notifications > Python → make sure "Allow Notifications" is ON
2. Check log: `grep PUBLISHED ~/.local/share/cve-tracker/tracker.log`

### "Recheck Now" does nothing?
- Already checking (spinner should be showing)
- Network error — check log: `tail -5 ~/.local/share/cve-tracker/tracker.log`

### App not auto-starting after reboot?
1. Verify plist: `plutil -lint ~/Library/LaunchAgents/com.hoangphi.cve-tracker.plist`
2. Reload: `launchctl load ~/Library/LaunchAgents/com.hoangphi.cve-tracker.plist`
3. Check if another instance is blocking: `pgrep -fl cve_menubar`

### Two "CVE" icons on menu bar?
- One is from launchd, one from manual `start.command` — click Quit on one of them
- Only the launchd one will auto-restart

---

## When Both CVEs Are Published

Title changes to **CVE-PP**. You'll also get 2 macOS notifications (one per CVE).

To remove the tracker after both are published:
```bash
./setup.sh uninstall
```

---

## Technical Notes

- **Why not Desktop?** macOS sandboxing prevents launchd agents from reading
  files in `~/Desktop` without granting Full Disk Access to Python. Moving
  runtime files to `~/.local/share/` avoids this.
- **Why rumps?** Lightweight Python library for macOS menu bar apps. Uses
  PyObjC (AppKit/NSStatusBar) under the hood. Installed in a venv to avoid
  polluting system Python.
- **Why not Unicode icons?** rumps 0.4.0 on Python 3.9 has issues rendering
  some Unicode characters in the menu bar. ASCII text titles work reliably.
- **Line endings matter:** `.command` files must have Unix line endings (LF).
  Windows line endings (CRLF) cause `bad interpreter: /bin/bash^M` error.
