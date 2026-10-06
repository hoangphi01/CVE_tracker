"""Configuration loading — constants and config.json support."""

import json
import os
from pathlib import Path

# Data directory (runtime files: state, logs)
DATA_DIR = Path(os.environ.get(
    "CVE_TRACKER_DATA_DIR",
    os.path.expanduser("~/.local/share/cve-tracker"),
))

# Config search order: env var path → data dir → repo root
_CONFIG_SEARCH = [
    Path(os.environ["CVE_TRACKER_CONFIG"]) if "CVE_TRACKER_CONFIG" in os.environ else None,
    DATA_DIR / "config.json",
    Path(__file__).resolve().parent.parent / "config.json",
]


def _load_config():
    for p in _CONFIG_SEARCH:
        if p and p.exists():
            with open(p) as f:
                return json.load(f)
    return {}


_cfg = _load_config()

# CVE IDs to track
CVE_IDS = _cfg.get("cve_ids", ["CVE-2026-78840", "CVE-2026-78841"])

# API
API_URL = "https://cveawg.mitre.org/api/cve-id/{cve_id}"
USER_AGENT = _cfg.get("user_agent", "CVE-Tracker/1.0 (personal; 2-requests-per-day)")
REQUEST_TIMEOUT = _cfg.get("request_timeout", 30)

# Schedule: list of (hour, minute) pairs for auto-check
SCHEDULE_HOURS = [tuple(t) for t in _cfg.get("schedule_hours", [[9, 3], [15, 3]])]

# File paths
STATE_FILE = DATA_DIR / "state.json"
LOG_FILE = DATA_DIR / "tracker.log"
