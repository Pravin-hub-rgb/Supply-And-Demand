"""Unit tests for candle parsing and calendar aggregation."""

import pytest

from supplyndemand.candles import Candle, aggregate_to_timeframe, parse_upstox_candles, period_start

MONTHLY = [
    Candle("2025-01-01", 100, 110, 90, 105, 1000),
    Candle("2025-02-01", 105, 120, 100, 118, 2000),
    Candle("2025-03-01", 118, 125, 115, 122, 3000),
    Candle("2025-07-01", 200, 210, 190, 205, 4000),
    Candle("2025-12-01", 220, 230, 210, 225, 5000),
]


def test_parse_upstox_candles_sorts_and_validates():
    rows = [
        ["2025-02-01T00:00:00+05:30", 3, 4, 2, 3.5, 200, 0],
        ["2025-01-01T00:00:00+05:30", 1, 2, 0.5, 1.5, 100, 0],
    ]

    candles = parse_upstox_candles(rows)

    assert [candle.time for candle in candles] == ["2025-01-01", "2025-02-01"]
    assert candles[0].volume == 100


def test_parse_upstox_candles_rejects_bad_rows():
    with pytest.raises(ValueError, match="Bad Upstox candle at index 0"):
        parse_upstox_candles([["2025-01-01T00:00:00+05:30", 10, 5, 12, 9, 1]])


def test_aggregate_quarterly_uses_calendar_quarters():
    result = aggregate_to_timeframe(MONTHLY, "Q")

    assert [(candle.time, candle.open, candle.close, candle.volume) for candle in result] == [
        ("2025-01-01", 100, 122, 6000),
        ("2025-07-01", 200, 205, 4000),
        ("2025-10-01", 220, 225, 5000),
    ]
    assert result[0].high == 125
    assert result[0].low == 90


def test_aggregate_half_yearly_uses_january_and_july():
    result = aggregate_to_timeframe(MONTHLY, "HY")

    assert [(candle.time, candle.volume) for candle in result] == [
        ("2025-01-01", 6000),
        ("2025-07-01", 9000),
    ]


def test_aggregate_yearly_uses_calendar_years():
    result = aggregate_to_timeframe(MONTHLY, "Y")

    assert len(result) == 1
    candle = result[0]
    assert (candle.time, candle.open, candle.close, candle.volume) == ("2025-01-01", 100, 225, 15000)


def test_aggregate_native_timeframes_pass_through():
    candles = [Candle("2026-01-01", 10, 12, 9, 11, 100)]

    assert aggregate_to_timeframe(candles, "D") == candles
    assert aggregate_to_timeframe(candles, "W") == candles
    assert aggregate_to_timeframe(candles, "M") == candles


def test_period_start_rejects_unknown_timeframe():
    with pytest.raises(ValueError):
        period_start("2025-01-01", "Z")
