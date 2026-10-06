"""MITRE CVE API client."""

import json
import urllib.request
import urllib.error

from .config import API_URL, USER_AGENT, REQUEST_TIMEOUT
from .state import log


def check_cve(cve_id):
    """Query CVE API for current state. Returns state string or None on error."""
    url = API_URL.format(cve_id=cve_id)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            return data.get("state", "UNKNOWN")
    except urllib.error.HTTPError as e:
        log(f"  HTTP error for {cve_id}: {e.code}")
        return None
    except Exception as e:
        log(f"  Error checking {cve_id}: {e}")
        return None
