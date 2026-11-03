"""API wiring tests using a temporary SQLite database."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from supplyndemand.api import create_app
from supplyndemand.candles import Candle
from supplyndemand.config import DownloadSettings, Settings
from supplyndemand.db import connect, init_db
from supplyndemand.repository import upsert_candles, upsert_instruments


def make_settings(tmp_path):
    return Settings(
        root=tmp_path,
        timeframes=["Y", "HY", "Q", "M", "W", "D"],
        database_path=tmp_path / "data" / "test.db",
        seed_path=tmp_path / "config" / "nifty50.json",
        daily_history_years=2,
        weekly_history_years=2,
        download=DownloadSettings(
            pacing_seconds=0,
            request_timeout_seconds=1,
            retry_attempts=1,
            initial_cooldown_seconds=1,
            max_cooldown_seconds=2,
            max_attempts_per_request=1,
        ),
    )


def seed_database(settings):
    init_db(settings.database_path)
    constituent = {
        "symbol": "RELIANCE",
        "name": "Reliance Industries Ltd.",
        "industry": "Oil",
        "isin": "INE002A01018",
        "instrument_key": "NSE_EQ|INE002A01018",
    }
    candles = [
        Candle("2026-01-01", 100, 110, 90, 105, 100),
        Candle("2026-02-01", 105, 120, 100, 118, 200),
        Candle("2026-07-01", 200, 210, 190, 205, 400),
    ]
    with connect(settings.database_path) as conn:
        upsert_instruments(conn, [constituent])
        upsert_candles(conn, constituent["instrument_key"], "M", candles)


@pytest.fixture
def client(tmp_path):
    settings = make_settings(tmp_path)
    seed_database(settings)
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_instruments(client):
    response = client.get("/api/instruments")
    assert response.status_code == 200
    assert response.json()[0]["symbol"] == "RELIANCE"


def test_unknown_symbol_returns_404(client):
    response = client.get("/api/candles/NOSUCH?timeframe=D")
    assert response.status_code == 404


def test_invalid_timeframe_returns_400(client):
    response = client.get("/api/candles/RELIANCE?timeframe=X")
    assert response.status_code == 400


def test_monthly_candles(client):
    response = client.get("/api/candles/RELIANCE?timeframe=M")
    assert response.status_code == 200
    assert [candle["time"] for candle in response.json()["candles"]] == ["2026-01-01", "2026-02-01", "2026-07-01"]


def test_yearly_is_derived_from_monthly(client):
    response = client.get("/api/candles/RELIANCE?timeframe=HY")
    assert response.status_code == 200
    assert [candle["time"] for candle in response.json()["candles"]] == ["2026-01-01", "2026-07-01"]
