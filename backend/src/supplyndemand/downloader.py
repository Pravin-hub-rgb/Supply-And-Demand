"""Download and cache candles for the configured Nifty 50 seed."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from .config import Settings
from .rate_limit import TokenPool
from .repository import upsert_candles, upsert_instruments, delete_candles_before
from .upstox import history_range

logger = logging.getLogger(__name__)
NATIVE_TIMEFRAMES = ("M", "W", "D")
EXPECTED_CONSTITUENTS = 50

Fetcher = Callable[[str, str, date, date], object]


def load_seed(seed_path: Path) -> list[dict]:
    """Read and validate config/nifty50.json."""
    try:
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        constituents = seed["constituents"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read Nifty 50 seed {seed_path}: {exc}") from exc
    if not isinstance(constituents, list) or len(constituents) != EXPECTED_CONSTITUENTS:
        raise RuntimeError(f"Seed {seed_path} must contain exactly {EXPECTED_CONSTITUENTS} constituents")
    return constituents


def download_seeded_symbols(
    conn: sqlite3.Connection,
    settings: Settings,
    tokens: list[str],
    symbols: Iterable[str] | None = None,
    fetcher: Fetcher | None = None,
) -> dict:
    """Download/upsert candles; return a summary with failures instead of hiding them."""
    seed = load_seed(settings.seed_path)
    upsert_instruments(conn, seed)
    wanted = {symbol.upper() for symbol in symbols} if symbols else None
    pool = TokenPool(tokens, settings.download)
    candle_fetcher = fetcher or _make_upstox_fetcher(pool, settings)
    today = date.today()
    summary = {"downloaded": {"D": 0, "W": 0, "M": 0}, "failures": []}

    for symbol in seed:
        if wanted and symbol["symbol"].upper() not in wanted:
            continue
        for timeframe in NATIVE_TIMEFRAMES:
            _download_one(conn, settings, candle_fetcher, symbol, timeframe, today, summary)
    return summary


def _download_one(conn: sqlite3.Connection, settings: Settings, fetcher: Fetcher, symbol: dict, timeframe: str, today: date, summary: dict) -> None:
    from_date, to_date = history_range(timeframe, today, settings.daily_history_years, settings.weekly_history_years)
    try:
        candles = fetcher(symbol["instrument_key"], timeframe, from_date, to_date)
        if timeframe in {"D", "W"}:
            delete_candles_before(conn, symbol["instrument_key"], timeframe, from_date.isoformat())
        inserted = upsert_candles(conn, symbol["instrument_key"], timeframe, candles)
    except Exception as exc:
        detail = f"{symbol['symbol']} {timeframe}: {exc}"
        logger.error("Candle download failed: %s", detail)
        summary["failures"].append(detail)
        return
    summary["downloaded"][timeframe] += inserted
    logger.info("Downloaded %s %s candles for %s", inserted, timeframe, symbol["symbol"])


def _make_upstox_fetcher(pool: TokenPool, settings: Settings) -> Fetcher:
    from .upstox import fetch_candles

    def fetch(instrument_key: str, timeframe: str, from_date: date, to_date: date) -> object:
        return fetch_candles(pool, settings.download, instrument_key, timeframe, from_date, to_date)

    return fetch
