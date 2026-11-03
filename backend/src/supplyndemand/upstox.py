"""Upstox V3 historical candle client with token-pool retry handling."""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any
from urllib.parse import quote

import requests

from .candles import Candle, parse_upstox_candles
from .config import DownloadSettings
from .rate_limit import TokenPool

V3_HISTORICAL_BASE = "https://api.upstox.com/v3/historical-candle"
TIMEFRAME_TO_PATH = {"D": "days/1", "W": "weeks/1", "M": "months/1"}
MONTHLY_START = date(2000, 1, 1)
logger = logging.getLogger(__name__)


class UpstoxError(RuntimeError):
    """Raised when Upstox cannot return a usable response."""


def history_range(timeframe: str, today: date, daily_years: int, weekly_years: int) -> tuple[date, date]:
    if timeframe == "M":
        return MONTHLY_START, today
    years = daily_years if timeframe == "D" else weekly_years
    return date(today.year - years, today.month, today.day), today


def fetch_candles(
    pool: TokenPool,
    settings: DownloadSettings,
    instrument_key: str,
    timeframe: str,
    from_date: date,
    to_date: date,
) -> list[Candle]:
    if timeframe not in TIMEFRAME_TO_PATH:
        raise ValueError(f"Unsupported native timeframe {timeframe!r}")
    url = _historical_url(instrument_key, TIMEFRAME_TO_PATH[timeframe], from_date, to_date)
    body = _get_json(pool, settings, url)
    rows = (body.get("data") or {}).get("candles") or []
    if not isinstance(rows, list):
        raise UpstoxError("Upstox response data.candles is not a list")
    return parse_upstox_candles(rows)


def _historical_url(instrument_key: str, api_path: str, from_date: date, to_date: date) -> str:
    encoded_key = quote(instrument_key, safe="")
    return f"{V3_HISTORICAL_BASE}/{encoded_key}/{api_path}/{to_date.isoformat()}/{from_date.isoformat()}"


def _get_json(pool: TokenPool, settings: DownloadSettings, url: str) -> dict[str, Any]:
    last_error = "unknown error"
    for attempt in range(1, settings.max_attempts_per_request + 1):
        state = pool.acquire()
        try:
            response = requests.get(url, headers=_headers(state.token), timeout=settings.request_timeout_seconds)
        except requests.RequestException as exc:
            last_error = f"network error: {exc.__class__.__name__}"
            _sleep_backoff(attempt)
            continue

        if response.status_code == 200:
            return _success_body(response, pool, state)
        if response.status_code == 401:
            pool.mark_dead(state)
            last_error = "token rejected with 401"
            continue
        if response.status_code == 429:
            pool.mark_rate_limited(state)
            last_error = "rate limited with 429"
            continue
        if response.status_code >= 500:
            last_error = f"server error http_{response.status_code}"
            _sleep_backoff(attempt)
            continue
        raise UpstoxError(f"Upstox returned http_{response.status_code}: {response.text[:200]}")

    raise UpstoxError(f"Upstox request failed after {settings.max_attempts_per_request} attempts: {last_error}")


def _success_body(response: requests.Response, pool: TokenPool, state: Any) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise UpstoxError("Upstox returned invalid JSON") from exc
    if str(body.get("status", "success")).lower() not in ("success", ""):
        raise UpstoxError(f"Upstox returned status {body.get('status')}")
    pool.record_success(state)
    return body


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(0.5 * attempt, 5.0))
