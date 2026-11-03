"""Unit tests for per-token pacing and cooldowns."""

from supplyndemand.config import DownloadSettings
from supplyndemand.rate_limit import TokenPool


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_settings():
    return DownloadSettings(
        pacing_seconds=0,
        request_timeout_seconds=1,
        retry_attempts=1,
        initial_cooldown_seconds=10,
        max_cooldown_seconds=30,
        max_attempts_per_request=3,
    )


def test_acquire_returns_least_recently_used_token():
    clock = FakeClock()
    pool = TokenPool(["token-a" * 10, "token-b" * 10], make_settings(), clock=clock)

    first = pool.acquire()
    clock.advance(1)
    second = pool.acquire()

    assert first.token != second.token


def test_rate_limited_token_is_cooled_down():
    clock = FakeClock()
    pool = TokenPool(["token-a" * 10], make_settings(), clock=clock)

    state = pool.acquire()
    pool.mark_rate_limited(state)

    assert state.status == "cooling"
    assert state.cooldown_until == 10


def test_all_dead_tokens_raise():
    pool = TokenPool(["token-a" * 10], make_settings(), clock=FakeClock())
    state = pool.acquire()
    pool.mark_dead(state)

    try:
        pool.acquire()
    except RuntimeError as exc:
        assert "dead" in str(exc).lower()
    else:
        raise AssertionError("expected RuntimeError")
