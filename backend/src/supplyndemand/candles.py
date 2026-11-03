"""Candle parsing and calendar aggregation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

INTRADAY_FORMATS = ("%Y-%m-%d",)
DERIVED_TIMEFRAMES = {"Q", "HY", "Y"}
NATIVE_TIMEFRAMES = {"D", "W", "M"}
ALL_TIMEFRAMES = NATIVE_TIMEFRAMES | DERIVED_TIMEFRAMES
IST = timezone(timedelta(hours=5, minutes=30))


@dataclass(frozen=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


def parse_upstox_candles(rows: list[list[Any]]) -> list[Candle]:
    """Validate Upstox candle arrays and return candles sorted by time ascending."""
    candles: list[Candle] = []
    for index, row in enumerate(rows):
        try:
            candles.append(_parse_row(row))
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"Bad Upstox candle at index {index}: {exc}") from exc
    candles.sort(key=lambda candle: candle.time)
    return candles


def aggregate_monthly(candles: list[Candle], timeframe: str) -> list[Candle]:
    """Aggregate monthly candles into calendar quarters, half-years, or years."""
    if timeframe not in DERIVED_TIMEFRAMES:
        raise ValueError(f"Cannot aggregate to {timeframe!r}")
    groups: dict[str, list[Candle]] = {}
    for candle in sorted(candles, key=lambda item: item.time):
        groups.setdefault(period_start(candle.time, timeframe), []).append(candle)
    return [_combine(timeframe, start, period) for start, period in sorted(groups.items())]


def aggregate_to_timeframe(candles: list[Candle], timeframe: str) -> list[Candle]:
    if timeframe == "M":
        return list(candles)
    if timeframe in DERIVED_TIMEFRAMES:
        return aggregate_monthly(candles, timeframe)
    raise ValueError(f"Unsupported timeframe {timeframe!r}")


def period_start(time_str: str, timeframe: str) -> str:
    day = date.fromisoformat(time_str[:10])
    if timeframe == "Q":
        return date(day.year, ((day.month - 1) // 3) * 3 + 1, 1).isoformat()
    if timeframe == "HY":
        return date(day.year, 1 if day.month <= 6 else 7, 1).isoformat()
    if timeframe == "Y":
        return date(day.year, 1, 1).isoformat()
    raise ValueError(f"Unsupported derived timeframe {timeframe!r}")


def _parse_row(row: list[Any]) -> Candle:
    if not isinstance(row, list) or len(row) < 6:
        raise ValueError("expected at least 6 fields")
    values = [float(row[index]) for index in range(1, 6)]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("OHLCV contains non-finite values")
    open_, high, low, close, volume = values
    if low > high:
        raise ValueError("low is greater than high")
    return Candle(time=_candle_date(row[0]), open=open_, high=high, low=low, close=close, volume=int(volume))


def _candle_date(value: Any) -> str:
    if isinstance(value, str):
        return datetime.fromisoformat(value).date().isoformat()
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000 if value > 1e12 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone(IST).date().isoformat()
    raise ValueError(f"unsupported candle time {value!r}")


def _combine(timeframe: str, start: str, period: list[Candle]) -> Candle:
    return Candle(
        time=start,
        open=period[0].open,
        high=max(candle.high for candle in period),
        low=min(candle.low for candle in period),
        close=period[-1].close,
        volume=sum(candle.volume for candle in period),
    )
