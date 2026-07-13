"""
serper_budget.py — hard daily cap on Serper API calls.

Serper's free pool is a one-time credit balance that does NOT replenish. A single
scan (and especially an Excel batch of hundreds of vendors × several queries each)
can drain the whole pool in one run. This module enforces a per-calendar-day
ceiling so no single run can exhaust the pool in one go.

Every SerperAPI.search() call reserves budget here first. Once the day's ceiling
is reached, further calls no-op gracefully (return empty) and the scan still
completes on its other, free sources (GDELT, OpenSanctions, Wikipedia, WHOIS…).

State persists in serper_budget.json (CWD = backend/) and rolls over
automatically at the start of each calendar day.
"""

import json
import logging
import os
import threading
from datetime import date

logger = logging.getLogger(__name__)

BUDGET_FILE = "serper_budget.json"
# Max Serper calls per calendar day. Keep well under the free pool so it lasts
# many days. Tune via .env without touching code.
DAILY_CAP = int(os.getenv("SERPER_DAILY_CAP", "150"))


class SerperBudget:
    def __init__(self):
        self._lock = threading.Lock()
        self._today = date.today().isoformat()
        self._used = 0
        self._load()

    def _load(self):
        try:
            with open(BUDGET_FILE) as f:
                data = json.load(f)
            if data.get("date") == self._today:
                self._used = int(data.get("used", 0))
            else:
                self._save()   # stale day → reset file to today
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            self._save()

    def _save(self):
        try:
            with open(BUDGET_FILE, "w") as f:
                json.dump({"date": self._today, "used": self._used}, f)
        except OSError as e:
            logger.warning("Could not persist Serper budget: %s", e)

    def _rollover(self):
        today = date.today().isoformat()
        if today != self._today:
            self._today = today
            self._used = 0
            self._save()

    def remaining(self) -> int:
        with self._lock:
            self._rollover()
            return max(0, DAILY_CAP - self._used)

    def try_spend(self, n: int = 1) -> bool:
        """Reserve n calls. Returns False (spending nothing) if it would exceed the cap."""
        with self._lock:
            self._rollover()
            if self._used + n <= DAILY_CAP:
                self._used += n
                self._save()
                return True
            return False


# Global instance — imported by the Serper client.
serper_budget = SerperBudget()
