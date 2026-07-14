"""
gemini_budget.py — daily cap on Gemini API usage for the free tier.

The free tier has limited requests and tokens per day. To keep a prototype demo
safe, this caps BOTH:
    - calls  per calendar day  (GEMINI_DAILY_CALL_CAP)
    - tokens per calendar day  (GEMINI_DAILY_TOKEN_CAP)

Each scan makes exactly one Gemini call. Before calling, llm_service reserves a
call here; after the response, it records the actual tokens used. When either cap
is reached, further scans fall back to the zero-token heuristic summaries and
spend nothing. Both counters reset automatically at the start of each day.

State persists in gemini_budget.json (CWD = backend/).
"""

import json
import logging
import os
import threading
from datetime import date

logger = logging.getLogger(__name__)

BUDGET_FILE = "gemini_budget.json"
# Max Gemini requests per day. One scan = one request, so this is "AI scans/day".
CALL_CAP  = int(os.getenv("GEMINI_DAILY_CALL_CAP", "25"))
# Max Gemini tokens per day (prompt + response). Safety net so a few big scans
# can't drain the daily token allowance.
TOKEN_CAP = int(os.getenv("GEMINI_DAILY_TOKEN_CAP", "200000"))


class GeminiBudget:
    def __init__(self):
        self._lock = threading.Lock()
        self._today = date.today().isoformat()
        self._calls = 0
        self._tokens = 0
        self._load()

    def _load(self):
        try:
            with open(BUDGET_FILE) as f:
                data = json.load(f)
            if data.get("date") == self._today:
                self._calls = int(data.get("calls", 0))
                self._tokens = int(data.get("tokens", 0))
            else:
                self._save()
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            self._save()

    def _save(self):
        try:
            with open(BUDGET_FILE, "w") as f:
                json.dump({"date": self._today, "calls": self._calls, "tokens": self._tokens}, f)
        except OSError as e:
            logger.warning("Could not persist Gemini budget: %s", e)

    def _rollover(self):
        today = date.today().isoformat()
        if today != self._today:
            self._today = today
            self._calls = 0
            self._tokens = 0
            self._save()

    def can_call(self) -> bool:
        """True if another Gemini call is allowed under both caps."""
        with self._lock:
            self._rollover()
            return self._calls < CALL_CAP and self._tokens < TOKEN_CAP

    def can_afford(self, est_tokens: int) -> bool:
        """True if a call costing roughly `est_tokens` still fits under both caps.

        Unlike can_call(), this checks the cap against the projected total, so an
        oversized scan is rejected BEFORE it spends the rest of the day's tokens.
        """
        with self._lock:
            self._rollover()
            return self._calls < CALL_CAP and self._tokens + max(0, int(est_tokens)) <= TOKEN_CAP

    def reserve(self, est_tokens: int):
        """Charge one call plus its estimated tokens, atomically, before the API call.

        Reserving up-front means a call that fails or times out still counts against
        the budget — the tokens were spent regardless of whether we got a response.
        reconcile() later corrects the estimate to the actual figure.
        """
        with self._lock:
            self._rollover()
            self._calls += 1
            self._tokens += max(0, int(est_tokens))
            self._save()

    def reconcile(self, est_tokens: int, actual_tokens: int):
        """Replace the reserved estimate with the actual usage, after the response."""
        with self._lock:
            self._rollover()
            delta = max(0, int(actual_tokens)) - max(0, int(est_tokens))
            self._tokens = max(0, self._tokens + delta)
            self._save()

    def reserve_call(self):
        """Count one request. Call this immediately before hitting the API."""
        with self._lock:
            self._rollover()
            self._calls += 1
            self._save()

    def add_tokens(self, n: int):
        """Record actual tokens spent, after the response returns."""
        with self._lock:
            self._rollover()
            self._tokens += max(0, int(n))
            self._save()

    def status(self) -> dict:
        with self._lock:
            self._rollover()
            return {
                "date": self._today,
                "calls_used": self._calls, "calls_cap": CALL_CAP,
                "tokens_used": self._tokens, "tokens_cap": TOKEN_CAP,
            }


# Global instance — imported by llm_service.
gemini_budget = GeminiBudget()
