"""Per-token pacing and cooldowns for Upstox downloads."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from .config import DownloadSettings


@dataclass
class TokenState:
    token: str
    tail: str
    status: str = "active"
    cooldown_until: float = 0.0
    consecutive_429: int = 0
    requests_made: int = 0
    last_used: float = 0.0


class TokenPool:
    """Round-robin token pool with per-token pacing and exponential 429 cooldowns."""

    def __init__(self, tokens: list[str], settings: DownloadSettings, clock: Callable[[], float] = time.monotonic) -> None:
        if not tokens:
            raise ValueError("TokenPool requires at least one token")
        self._settings = settings
        self._clock = clock
        self._cursor = 0
        self._tokens = [TokenState(token=token, tail=token[-4:]) for token in tokens]

    def acquire(self) -> TokenState:
        """Return the next usable token, waiting for cooldowns if necessary."""
        while True:
            now = self._clock()
            self._reactivate_cooled_tokens(now)
            if all(state.status == "dead" for state in self._tokens):
                raise RuntimeError("All Upstox tokens are dead or rejected")
            for offset in range(len(self._tokens)):
                index = (self._cursor + offset) % len(self._tokens)
                state = self._tokens[index]
                if self._is_ready(state, now):
                    state.last_used = now
                    self._cursor = (index + 1) % len(self._tokens)
                    return state
            time.sleep(self._seconds_until_ready(now))

    def record_success(self, state: TokenState) -> None:
        state.consecutive_429 = 0
        state.requests_made += 1
        state.status = "active"

    def mark_dead(self, state: TokenState) -> None:
        state.status = "dead"
        state.cooldown_until = 0.0

    def mark_rate_limited(self, state: TokenState) -> None:
        state.status = "cooling"
        state.consecutive_429 += 1
        cooldown = self._settings.initial_cooldown_seconds * (2 ** (state.consecutive_429 - 1))
        state.cooldown_until = self._clock() + min(cooldown, self._settings.max_cooldown_seconds)

    def _reactivate_cooled_tokens(self, now: float) -> None:
        for state in self._tokens:
            if state.status == "cooling" and now >= state.cooldown_until:
                state.status = "active"
                state.cooldown_until = 0.0

    def _is_ready(self, state: TokenState, now: float) -> bool:
        return state.status == "active" and now - state.last_used >= self._settings.pacing_seconds

    def _seconds_until_ready(self, now: float) -> float:
        waits = [
            max(state.cooldown_until - now, self._settings.pacing_seconds - (now - state.last_used))
            for state in self._tokens
            if state.status != "dead"
        ]
        return max(0.05, min(waits) if waits else 1.0)
