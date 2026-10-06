# CVE Tracker

![macOS](https://img.shields.io/badge/macOS-000?logo=apple&logoColor=white)
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A persistent macOS menu bar app that tracks CVE publication status via the MITRE API.
Get notified the moment your CVEs go from **RESERVED** to **PUBLISHED**.

```
 CVE-RR
 ──────────────────────────
  CVE-2026-78840: RESERVED       <- click opens cve.org
  CVE-2026-78841: RESERVED       <- click opens cve.org
  ─────────────────────────
  Last: 13:26 17/09
  ─────────────────────────
  Recheck Now
  [CVE-XXXX-XXXXX  Enter]        <- lookup any CVE
    CVE-2024-1234: PUBLISHED
  ─────────────────────────
  Quit
```

## Features

- **Menu bar status** — shows `CVE-RR` (both reserved), `CVE-PP` (both published), etc.
- **Auto-check** at configurable times (default: 9:03 and 15:03 daily)
- **Manual recheck** via dropdown menu
- **Lookup any CVE** — inline text field, type an ID and press Enter
- **macOS notifications** with sound when status changes
- **Auto-start at login** via launchd (`RunAtLoad` + `KeepAlive`)
- **Survives sleep/wake** — missed checks run when the Mac wakes up
- **Click any CVE** to open its page on cve.org

## Quick Start

```bash
# Clone
git clone https://github.com/hoangphi01/CVE_tracker.git
cd CVE_tracker

# Install (creates venv, installs deps, sets up launchd)
chmod +x scripts/install.sh
./scripts/install.sh
```

The menu bar icon appears immediately. Edit `~/.local/share/cve-tracker/config.json` to track your own CVEs.

## Configuration

Edit `config.json` (or the copy at `~/.local/share/cve-tracker/config.json`):

```json
{
  "cve_ids": ["CVE-2026-78840", "CVE-2026-78841"],
  "user_agent": "CVE-Tracker/1.0 (personal; 2-requests-per-day)",
  "request_timeout": 30,
  "schedule_hours": [[9, 3], [15, 3]]
}
```

| Key | Description |
|-----|-------------|
| `cve_ids` | List of CVE IDs to track |
| `user_agent` | HTTP User-Agent for API requests |
| `request_timeout` | Seconds before request timeout |
| `schedule_hours` | `[[hour, minute], ...]` pairs for auto-check times |

## Menu Bar Codes

| Title | CVE-78840 | CVE-78841 |
|-------|-----------|-----------|
| **CVE-RR** | RESERVED | RESERVED |
| **CVE-PR** | PUBLISHED | RESERVED |
| **CVE-RP** | RESERVED | PUBLISHED |
| **CVE-PP** | PUBLISHED | PUBLISHED |
| **CVE-??** | Unknown | Unknown |

During a check, the title shows a spinner: `CVE /` -> `CVE -` -> `CVE \` -> `CVE |`

## How It Works

1. **Login** -> launchd starts the app automatically
2. Every 60s, the scheduler checks if it's time for an auto-check
3. When triggered (scheduled or manual):
   - Queries `https://cveawg.mitre.org/api/cve-id/{CVE-ID}` for each CVE
   - 3-second polite delay between requests
   - Updates menu, saves state, logs the result
   - Sends macOS notification if status changed
4. State persists in `~/.local/share/cve-tracker/state.json`

## CLI Usage

```bash
# Quick check from terminal (no menu bar)
cve-check

# Or run directly
python3 -m cve_tracker.cli
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Menu bar icon not showing | `launchctl list \| grep cve-tracker` — check if loaded |
| No notifications | System Settings > Notifications > Python > Allow |
| App not starting after reboot | `./scripts/install.sh` to reinstall launchd plist |
| Two menu bar icons | Click Quit on one — only the launchd instance auto-restarts |

See [docs/USAGE.md](docs/USAGE.md) for detailed troubleshooting and maintenance commands.

## Uninstall

```bash
./scripts/uninstall.sh
```

## License

[MIT](LICENSE) - Hoang Phi
