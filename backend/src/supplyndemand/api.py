"""FastAPI routes for the local SupplynDemand app."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .candles import ALL_TIMEFRAMES, aggregate_to_timeframe
from .config import Settings, load_settings
from .db import connect, migrate
from .repository import fetch_candles, fetch_instruments, find_instrument


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    with connect(app_settings.database_path) as conn:
        migrate(conn)
    app = FastAPI(title="SupplynDemand", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3005", "http://127.0.0.1:3005"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.state.settings = app_settings
    app.get("/api/health")(health)
    app.get("/api/instruments")(instruments)
    app.get("/api/candles/{symbol}")(candles)
    return app


def health(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    with connect(settings.database_path) as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "service": "supplyndemand"}


def instruments(settings: Settings = Depends(get_settings)) -> list[dict[str, Any]]:
    with connect(settings.database_path) as conn:
        return fetch_instruments(conn)


def candles(
    symbol: str,
    timeframe: str = Query(default="D"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    normalized = timeframe.upper()
    if normalized not in ALL_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"timeframe must be one of {sorted(ALL_TIMEFRAMES)}")
    with connect(settings.database_path) as conn:
        instrument = find_instrument(conn, symbol.upper())
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Unknown Nifty 50 symbol: {symbol.upper()}")
        native_timeframe = "M" if normalized in {"Q", "HY", "Y"} else normalized
        rows = fetch_candles(conn, instrument["instrument_key"], native_timeframe)
    derived_rows = aggregate_to_timeframe(rows, normalized)
    return {
        "symbol": instrument["symbol"],
        "timeframe": normalized,
        "empty": len(derived_rows) == 0,
        "candles": [candle.to_dict() for candle in derived_rows],
    }
