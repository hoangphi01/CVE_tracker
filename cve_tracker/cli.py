#!/usr/bin/env python3
"""CVE Tracker — CLI checker."""

import subprocess
import sys
import time

from .config import CVE_IDS
from .api import check_cve
from .state import log, load_state, save_state


def notify(title, message):
    """Send macOS notification via osascript."""
    script = (
        f'display notification "{message}" '
        f'with title "{title}" '
        f'sound name "Glass"'
    )
    subprocess.run(["osascript", "-e", script], capture_output=True)


def main():
    log("CVE Tracker running (CLI)")
    print("CVE Tracker — CLI check")
    state = load_state()
    any_changed = False

    for cve_id in CVE_IDS:
        old_state = state.get(cve_id, "UNKNOWN")
        new_state = check_cve(cve_id)

        if new_state is None:
            msg = f"  {cve_id}: failed to check (network error?)"
            log(msg)
            print(msg)
            continue

        log(f"  {cve_id}: {new_state}")
        print(f"  {cve_id}: {new_state}")

        if new_state != old_state:
            any_changed = True
            state[cve_id] = new_state
            state[f"{cve_id}_changed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            if new_state == "PUBLISHED":
                notify(f"{cve_id} PUBLISHED!", "Your CVE has been published! Visit cve.org to see it.")
                log(f"  >>> {cve_id} IS NOW PUBLISHED! <<<")
            elif new_state == "REJECTED":
                notify(f"{cve_id} Rejected", "Status changed to REJECTED. Check MITRE email.")
                log(f"  >>> {cve_id} was REJECTED <<<")
            else:
                notify(f"{cve_id} Status Changed", f"Status: {old_state} -> {new_state}")
                log(f"  Status changed: {old_state} -> {new_state}")
        else:
            log(f"  {cve_id}: no change (still {new_state})")

        time.sleep(3)

    if any_changed:
        save_state(state)
    elif not state:
        for cve_id in CVE_IDS:
            if cve_id not in state:
                state[cve_id] = "RESERVED"
        save_state(state)

    all_published = all(state.get(cve_id) == "PUBLISHED" for cve_id in CVE_IDS)
    if all_published:
        print("Both CVEs published! You can unload the launchd job.")
        log("Both CVEs published!")

    log("Done.\n")


if __name__ == "__main__":
    main()
