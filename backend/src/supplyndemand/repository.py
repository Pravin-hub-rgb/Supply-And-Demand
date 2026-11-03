"""Persistence helpers for instruments and candles."""

from __future__ import annotations

import sqlite3
from typing import Any

from .candles import Candle


def upsert_instruments(conn: sqlite3.Connection, constituents: list[dict[str, Any]]) -> int:
    rows = [
        (
            row["symbol"],
            row["name"],
            row.get("industry"),
            row["isin"],
            row["instrument_key"],
        )
        for row in constituents
    ]
    conn.executemany(
        """
        INSERT INTO instruments (symbol, name, industry, isin, instrument_key, is_nifty50)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(symbol) DO UPDATE SET
            name = excluded.name,
            industry = excluded.industry,
            isin = excluded.isin,
            instrument_key = excluded.instrument_key,
            is_nifty50 = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def upsert_candles(conn: sqlite3.Connection, instrument_key: str, timeframe: str, candles: list[Candle]) -> int:
    rows = [
        (instrument_key, timeframe, candle.time, candle.open, candle.high, candle.low, candle.close, candle.volume)
        for candle in candles
    ]
    conn.executemany(
        """
        INSERT INTO candles (instrument_key, timeframe, candle_time, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(instrument_key, timeframe, candle_time) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            volume = excluded.volume
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def delete_candles_before(conn: sqlite3.Connection, instrument_key: str, timeframe: str, cutoff: str) -> int:
    cursor = conn.execute(
        "DELETE FROM candles WHERE instrument_key = ? AND timeframe = ? AND candle_time < ?",
        (instrument_key, timeframe, cutoff),
    )
    conn.commit()
    return cursor.rowcount


def fetch_candles(conn: sqlite3.Connection, instrument_key: str, timeframe: str) -> list[Candle]:
    rows = conn.execute(
        """
        SELECT candle_time, open, high, low, close, volume
        FROM candles
        WHERE instrument_key = ? AND timeframe = ?
        ORDER BY candle_time
        """,
        (instrument_key, timeframe),
    ).fetchall()
    return [
        Candle(time=row["candle_time"], open=row["open"], high=row["high"], low=row["low"], close=row["close"], volume=row["volume"])
        for row in rows
    ]


def fetch_instruments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT symbol, name, industry, isin, instrument_key
        FROM instruments
        WHERE is_nifty50 = 1
        ORDER BY symbol
        """
    ).fetchall()
    return [dict(row) for row in rows]


def find_instrument(conn: sqlite3.Connection, symbol: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT symbol, name, industry, isin, instrument_key FROM instruments WHERE symbol = ?",
        (symbol,),
    ).fetchone()
    return dict(row) if row else None
