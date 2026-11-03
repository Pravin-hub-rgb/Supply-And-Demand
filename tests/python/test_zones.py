"""Unit tests for automatic yearly zone detection."""

from supplyndemand.candles import Candle
from supplyndemand.zones import (
    DetectedZone,
    detect_zones,
    select_nearest,
)


def candle(time, open_, high, low, close):
    return Candle(time, float(open_), float(high), float(low), float(close), 1000)


def test_detects_rbr_demand_zone_with_body_top_and_wick_bottom():
    candles = [
        candle("2020-01-01", 100, 114, 98, 112),
        candle("2021-01-01", 108, 115, 104, 112),
        candle("2022-01-01", 112, 130, 110, 126),
    ]

    zones = detect_zones(candles)

    assert [zone.pattern for zone in zones] == ["RBR"]
    assert zones[0].type == "demand"
    assert zones[0].top == 112
    assert zones[0].bottom == 104
    assert zones[0].start_index == 1


def test_detects_rbd_supply_zone_with_body_bottom_and_wick_top():
    candles = [
        candle("2020-01-01", 100, 114, 98, 112),
        candle("2021-01-01", 112, 116, 104, 108),
        candle("2022-01-01", 108, 112, 84, 88),
    ]

    zones = detect_zones(candles)

    assert [zone.pattern for zone in zones] == ["RBD"]
    assert zones[0].type == "supply"
    assert zones[0].bottom == 108
    assert zones[0].top == 116


def test_zone_is_rejected_when_later_wick_touches_it():
    candles = [
        candle("2020-01-01", 100, 114, 98, 112),
        candle("2021-01-01", 108, 115, 104, 112),
        candle("2022-01-01", 112, 130, 110, 126),
        candle("2023-01-01", 126, 131, 103, 128),
    ]

    assert detect_zones(candles) == []


def test_rejects_base_runs_longer_than_seven_candles():
    candles = [candle("2020-01-01", 100, 114, 98, 112)]
    candles.extend(candle(f"{2020 + index + 1}-01-01", 110, 116, 104, 111) for index in range(8))
    candles.append(candle("2029-01-01", 111, 135, 110, 130))

    assert detect_zones(candles) == []


def test_select_nearest_keeps_closest_demand_and_supply():
    zones = [
        DetectedZone("RBR", "demand", 20, 10, 0, 2, "2020-01-01"),
        DetectedZone("DBR", "demand", 40, 30, 1, 3, "2021-01-01"),
        DetectedZone("RBD", "supply", 60, 50, 2, 4, "2022-01-01"),
        DetectedZone("DBD", "supply", 90, 80, 3, 5, "2023-01-01"),
    ]

    nearest = select_nearest(zones, latest_close=25)

    assert [zone.pattern for zone in nearest] == ["DBR", "RBD"]
