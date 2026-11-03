"""API tests for yearly zone detection."""

from fastapi.testclient import TestClient

from supplyndemand.api import create_app
from supplyndemand.candles import Candle
from supplyndemand.config import DownloadSettings, Settings
from supplyndemand.db import connect, init_db
from supplyndemand.repository import upsert_candles, upsert_instruments

INSTRUMENT = {
    "symbol": "RELIANCE",
    "name": "Reliance Industries Ltd.",
    "industry": "Oil",
    "isin": "INE002A01018",
    "instrument_key": "NSE_EQ|INE002A01018",
}


def make_settings(tmp_path):
    return Settings(
        root=tmp_path,
        timeframes=["Y", "HY", "Q", "M", "W", "D"],
        database_path=tmp_path / "data" / "test.db",
        seed_path=tmp_path / "config" / "nifty50.json",
        daily_history_years=2,
        weekly_history_years=2,
        download=DownloadSettings(0, 1, 1, 1, 2, 1),
    )


def add_year(conn, key, year, open_, high, low, close):
    candles = [
        Candle(f"{year}-{month:02d}-01", open_, high, low, close, 100)
        for month in range(1, 13)
    ]
    upsert_candles(conn, key, "M", candles)


def seed_rbr_pattern(settings):
    init_db(settings.database_path)
    with connect(settings.database_path) as conn:
        upsert_instruments(conn, [INSTRUMENT])
        key = INSTRUMENT["instrument_key"]
        add_year(conn, key, 2020, 100, 114, 98, 112)
        add_year(conn, key, 2021, 108, 115, 104, 112)
        add_year(conn, key, 2022, 112, 130, 110, 126)


def seed_empty(settings):
    init_db(settings.database_path)
    with connect(settings.database_path) as conn:
        upsert_instruments(conn, [INSTRUMENT])


def test_yearly_zone_endpoint_returns_nearest_rbr_zone(tmp_path):
    settings = make_settings(tmp_path)
    seed_rbr_pattern(settings)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/zones/RELIANCE?timeframe=Y")

    assert response.status_code == 200
    assert response.json()["empty"] is False
    assert response.json()["zones"] == [
        {
            "pattern": "RBR",
            "type": "demand",
            "top": 112.0,
            "bottom": 104.0,
            "startIndex": 1,
            "startTime": "2021-01-01",
            "completedIndex": 2,
        }
    ]


def test_zone_endpoint_rejects_invalid_timeframe(tmp_path):
    settings = make_settings(tmp_path)
    seed_empty(settings)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/zones/RELIANCE?timeframe=X")

    assert response.status_code == 400


def test_zone_endpoint_returns_empty_when_no_zone(tmp_path):
    settings = make_settings(tmp_path)
    seed_empty(settings)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/zones/RELIANCE?timeframe=Y")

    assert response.status_code == 200
    assert response.json()["zones"] == []
    assert response.json()["empty"] is True


def test_zone_endpoint_unknown_symbol(tmp_path):
    settings = make_settings(tmp_path)
    seed_empty(settings)

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/zones/NOSUCH?timeframe=Y")

    assert response.status_code == 404
