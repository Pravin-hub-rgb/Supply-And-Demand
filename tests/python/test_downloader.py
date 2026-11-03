"""Offline tests for the seeded downloader."""

import json
from pathlib import Path

from supplyndemand.candles import Candle
from supplyndemand.config import DownloadSettings, Settings
from supplyndemand.db import connect, init_db
from supplyndemand.downloader import download_seeded_symbols
from supplyndemand.repository import fetch_candles


def make_settings(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    seed = {
        "index": "NIFTY 50",
        "constituents": [
            {
                "symbol": f"SYM{i}",
                "name": f"Symbol {i}",
                "industry": "Test",
                "isin": f"INE0000000{i:02d}",
                "instrument_key": f"NSE_EQ|INE0000000{i:02d}",
            }
            for i in range(50)
        ],
    }
    seed_path = config_dir / "nifty50.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")
    return Settings(
        root=tmp_path,
        timeframes=["Y", "HY", "Q", "M", "W", "D"],
        database_path=tmp_path / "data" / "test.db",
        seed_path=seed_path,
        daily_history_years=2,
        weekly_history_years=2,
        download=DownloadSettings(0, 1, 1, 1, 2, 1),
    )


def fake_fetcher(_instrument_key, timeframe, _from_date, _to_date):
    return [Candle("2026-01-01", 1, 2, 0.5, 1.5, 100)]


def test_download_seeded_symbols_populates_database(tmp_path):
    settings = make_settings(tmp_path)
    init_db(settings.database_path)

    with connect(settings.database_path) as conn:
        summary = download_seeded_symbols(conn, settings, ["token" * 10], fetcher=fake_fetcher)
        rows = fetch_candles(conn, "NSE_EQ|INE000000000", "M")

    assert summary["failures"] == []
    assert summary["downloaded"]["M"] == 50
    assert len(rows) == 1
    assert rows[0].close == 1.5
