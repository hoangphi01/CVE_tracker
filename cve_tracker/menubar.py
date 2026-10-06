#!/usr/bin/env python3
"""CVE Tracker — macOS Menu Bar App."""

import os
import threading
import time
from datetime import datetime

import objc
from AppKit import NSFont, NSTextField, NSView
from Foundation import NSObject as _NSObject

import rumps

from .config import CVE_IDS, SCHEDULE_HOURS, save_config
from .api import check_cve
from .state import log, load_state, save_state


class _LookupHandler(_NSObject):
    """ObjC target for the inline lookup text field (Enter key fires action)."""

    def initWithApp_(self, app):
        self = objc.super(_LookupHandler, self).init()
        if self is not None:
            self._app = app
        return self

    def doLookup_(self, sender):
        text = sender.stringValue()
        cve_id = text.strip() if text else ""
        if cve_id:
            if not cve_id.upper().startswith("CVE-"):
                cve_id = f"CVE-{cve_id}"
            # Ensure dash after year: CVE-202678640 -> CVE-2026-78640
            parts = cve_id.split("-", 1)
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) > 4:
                parts[1] = parts[1][:4] + "-" + parts[1][4:]
                cve_id = "-".join(parts)
            sender.setStringValue_("")
            self._app.lookup_result.title = f"  Looking up {cve_id}..."
            threading.Thread(
                target=self._app._do_lookup, args=(cve_id,), daemon=True
            ).start()


class CVETrackerApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="CVE Tracker",
            title="CVE",
            quit_button=None,
        )

        self.state = load_state()
        self.checking = False
        self.cve_ids = list(CVE_IDS)

        # Build menu
        self.cve_items = {}
        for cve_id in self.cve_ids:
            st = self.state.get(cve_id, "?")
            item = rumps.MenuItem(f"{cve_id}: {st}", callback=self.open_cve)
            self.cve_items[cve_id] = item

        last = self.state.get("_last_check", "Never")
        self.last_check_item = rumps.MenuItem(f"Last: {last}")
        self.recheck_item = rumps.MenuItem("Recheck Now", callback=self.on_recheck)
        self._lookup_placeholder = rumps.MenuItem("lookup_tf")
        self.lookup_result = rumps.MenuItem("")
        self.settings_menu = self._build_settings_menu()
        self.quit_item = rumps.MenuItem("Quit", callback=self.on_quit)

        self.menu = [
            *self.cve_items.values(),
            None,
            self.last_check_item,
            None,
            self.recheck_item,
            self._lookup_placeholder,
            self.lookup_result,
            None,
            self.settings_menu,
            None,
            self.quit_item,
        ]

        self._setup_lookup_field()
        self._update_title()

    # ── Settings submenu ──────────────────────────────────

    def _build_settings_menu(self):
        settings = rumps.MenuItem("Settings")
        settings.add(rumps.MenuItem("Add CVE...", callback=self.on_add_cve))
        settings.add(None)  # separator
        for cve_id in self.cve_ids:
            settings.add(rumps.MenuItem(f"{cve_id}  ✕", callback=self.on_remove_cve))
        return settings

    def _rebuild_menu(self):
        self.menu.clear()

        self.cve_items = {}
        for cve_id in self.cve_ids:
            st = self.state.get(cve_id, "?")
            item = rumps.MenuItem(f"{cve_id}: {st}", callback=self.open_cve)
            self.cve_items[cve_id] = item

        self.settings_menu = self._build_settings_menu()

        self.menu = [
            *self.cve_items.values(),
            None,
            self.last_check_item,
            None,
            self.recheck_item,
            self._lookup_placeholder,
            self.lookup_result,
            None,
            self.settings_menu,
            None,
            self.quit_item,
        ]

        self._setup_lookup_field()
        self._update_title()

    @staticmethod
    def _normalize_cve_id(raw):
        """Normalize user input into a CVE ID, or return None."""
        cve_id = raw.strip()
        if not cve_id:
            return None
        if not cve_id.upper().startswith("CVE-"):
            cve_id = f"CVE-{cve_id}"
        parts = cve_id.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) > 4:
            parts[1] = parts[1][:4] + "-" + parts[1][4:]
            cve_id = "-".join(parts)
        return cve_id.upper()

    def on_add_cve(self, _):
        w = rumps.Window(
            title="Add CVE",
            message="Enter CVE ID (e.g. CVE-2024-1234):",
            default_text="CVE-",
            ok="Add",
            cancel="Cancel",
            dimensions=(260, 22),
        )
        resp = w.run()
        if resp.clicked:
            cve_id = self._normalize_cve_id(resp.text)
            if not cve_id:
                return
            if len(self.cve_ids) >= 5:
                rumps.alert("Limit reached", "Maximum 5 CVEs can be tracked at the same time.")
                return
            if cve_id in self.cve_ids:
                rumps.alert("Duplicate", f"{cve_id} is already tracked.")
                return
            self.cve_ids.append(cve_id)
            save_config(self.cve_ids)
            self._rebuild_menu()
            threading.Thread(target=self._do_check, daemon=True).start()

    def on_remove_cve(self, sender):
        cve_id = sender.title.replace("  ✕", "")
        if len(self.cve_ids) <= 1:
            rumps.alert("Cannot remove", "At least one CVE must be tracked.")
            return
        resp = rumps.alert(
            title="Remove CVE",
            message=f"Stop tracking {cve_id}?",
            ok="Remove",
            cancel="Cancel",
        )
        if resp == 1:  # OK
            self.cve_ids.remove(cve_id)
            save_config(self.cve_ids)
            self._rebuild_menu()

    def open_cve(self, sender):
        for cve_id, item in self.cve_items.items():
            if sender == item:
                os.system(f'open "https://www.cve.org/CVERecord?id={cve_id}"')
                break

    def on_recheck(self, _):
        if not self.checking:
            t = threading.Thread(target=self._do_check, daemon=True)
            t.start()

    def _setup_lookup_field(self):
        handler = _LookupHandler.alloc().initWithApp_(self)
        self._lookup_handler = handler  # prevent GC

        container = NSView.alloc().initWithFrame_(((0, 0), (250, 28)))
        tf = NSTextField.alloc().initWithFrame_(((12, 3), (226, 22)))
        tf.setPlaceholderString_("CVE-XXXX-XXXXX  Enter")
        tf.setFont_(NSFont.systemFontOfSize_(13))
        tf.setTarget_(handler)
        tf.setAction_(handler.doLookup_)
        container.addSubview_(tf)
        self._lookup_tf = tf

        self._lookup_placeholder._menuitem.setView_(container)

    def _do_lookup(self, cve_id):
        state = check_cve(cve_id)
        if state:
            self.lookup_result.title = f"  {cve_id}: {state}"
        else:
            self.lookup_result.title = f"  {cve_id}: network error"

    def on_quit(self, _):
        rumps.quit_application()

    @rumps.timer(60)
    def scheduler(self, _):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        for hour, minute in SCHEDULE_HOURS:
            slot_key = f"{today}-{hour}"
            already_done = self.state.get("_done_slots", [])
            if slot_key in already_done:
                continue
            if now.hour > hour or (now.hour == hour and now.minute >= minute):
                if not self.checking:
                    if "_done_slots" not in self.state:
                        self.state["_done_slots"] = []
                    self.state["_done_slots"].append(slot_key)
                    self.state["_done_slots"] = self.state["_done_slots"][-10:]
                    save_state(self.state)
                    log(f"Auto-check triggered for slot {hour}:{minute:02d}")
                    t = threading.Thread(target=self._do_check, daemon=True)
                    t.start()
                    break

    @rumps.timer(0.4)
    def spinner(self, _):
        if self.checking:
            frames = ["/", "-", "\\", "|"]
            idx = int(time.time() * 2.5) % len(frames)
            self.title = f"CVE {frames[idx]}"

    def _do_check(self):
        self.checking = True
        self.recheck_item.title = "Checking..."
        log("Check started")

        any_changed = False

        for cve_id in list(self.cve_ids):
            old = self.state.get(cve_id, "UNKNOWN")
            new = check_cve(cve_id)

            if new is None:
                log(f"  {cve_id}: network error")
                time.sleep(3)
                continue

            log(f"  {cve_id}: {new}")
            self.cve_items[cve_id].title = f"{cve_id}: {new}"

            if new != old:
                any_changed = True
                self.state[cve_id] = new
                self.state[f"{cve_id}_changed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                if new == "PUBLISHED":
                    rumps.notification(
                        f"{cve_id} PUBLISHED!",
                        "Your CVE is now public!",
                        "Click to visit cve.org",
                        sound=True,
                    )
                    log(f"  >>> {cve_id} PUBLISHED! <<<")
                elif new == "REJECTED":
                    rumps.notification(
                        f"{cve_id} Rejected",
                        "Status changed",
                        "Check MITRE email.",
                        sound=True,
                    )

            time.sleep(3)

        now_str = time.strftime("%H:%M %d/%m")
        self.state["_last_check"] = now_str
        self.last_check_item.title = f"Last: {now_str}"
        save_state(self.state)

        log("Check done.\n")
        self.checking = False
        self.recheck_item.title = "Recheck Now"
        self._update_title()

    def _update_title(self):
        codes = []
        for cve_id in self.cve_ids:
            s = self.state.get(cve_id, "?")
            if s == "PUBLISHED":
                codes.append("P")
            elif s == "RESERVED":
                codes.append("R")
            else:
                codes.append("?")
        self.title = f"CVE-{''.join(codes)}"


def main():
    app = CVETrackerApp()
    app.run()


if __name__ == "__main__":
    main()
