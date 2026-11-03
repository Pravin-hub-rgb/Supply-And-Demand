"""SQLite connection and schema for the local candle cache."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    isin TEXT NOT NULL UNIQUE,
    instrument_key TEXT NOT NULL UNIQUE,
    is_nifty50 INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candles (
    instrument_key TEXT NOT NULL,
    timeframe TEXT NOT NULL CHECK (timeframe IN ('D', 'W', 'M')),
    candle_time TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (instrument_key, timeframe, candle_time),
    FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
);

CREATE INDEX IF NOT EXISTS idx_candles_lookup
    ON candles (instrument_key, timeframe, candle_time);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        migrate(conn)
