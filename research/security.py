"""Supplementary in-process request limits for the independent research service.

NOT a substitute for ingress limits, bot mitigation, TLS, WAF or privacy review.
Peer IP is transiently held in memory, never written to disk. Do not trust
user-controlled forwarded IP headers here.
"""
from __future__ import annotations

from collections import deque
import threading
import time


class SlidingWindowLimiter:
    def __init__(self, max_keys: int = 4096):
        self.max_keys = max_keys
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self._checks = 0

    def allow(self, key: str, *, limit: int, window: float, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        with self._lock:
            self._checks += 1
            if self._checks % 100 == 0 or len(self._events) >= self.max_keys:
                for stale_key, previous in list(self._events.items()):
                    if not previous or (timestamp - previous[-1]) >= window:
                        del self._events[stale_key]
            if key not in self._events and len(self._events) >= self.max_keys:
                return False
            recent = self._events.setdefault(key, deque())
            while recent and timestamp - recent[0] >= window:
                recent.popleft()
            if len(recent) >= limit:
                return False
            recent.append(timestamp)
            return True


limiter = SlidingWindowLimiter()
