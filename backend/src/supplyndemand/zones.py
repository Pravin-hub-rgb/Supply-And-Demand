"""Automatic yearly supply/demand zone detection.

Detects heuristic strong-move / base / strong-move sequences and rejects any
zone whose rectangle is touched by a later wick. Zones are recalculated on
every request and are not persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .candles import Candle

STRONG_BODY_TO_RANGE = 0.45
BASE_BODY_TO_RANGE = 0.45
STRONG_AVERAGE_MULTIPLE = 1.5
AVERAGE_BODY_WINDOW = 20
MAX_BASE_CANDLES = 7

DEMAND_PATTERNS = frozenset({"RBR", "DBR"})
SUPPLY_PATTERNS = frozenset({"RBD", "DBD"})


@dataclass(frozen=True)
class CandleClass:
    """Strong/base classification for one candle."""

    time: str
    strong: bool
    base: bool
    direction: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "strong": self.strong,
            "base": self.base,
            "direction": self.direction,
        }


def classify_candles(candles: list[Candle]) -> list[CandleClass]:
    """Classify each candle as strong, base, or neither."""
    if not candles:
        return []
    bodies = [_body(candle) for candle in candles]
    averages = _average_bodies(bodies)
    ranges = [_range(candle) for candle in candles]
    true_ranges = [_true_range(candles, index) for index in range(len(candles))]
    atrs = [_atr(true_ranges, index) for index in range(len(true_ranges))]
    strengths = [
        _candle_strength(candles[index], bodies[index], averages[index], true_ranges[index], atrs[index])
        for index in range(len(candles))
    ]
    return [
        CandleClass(
            time=candles[index].time,
            strong=False if index == len(candles) - 1 else strengths[index][0],
            base=False if index == len(candles) - 1 else (not strengths[index][0] and _is_base(candles[index], atrs[index])),
            direction=0 if index == len(candles) - 1 else strengths[index][1],
        )
        for index in range(len(candles))
    ]
@dataclass(frozen=True)
class DetectedZone:
    """One fully detected and still-fresh pattern."""

    pattern: str
    type: str
    top: float
    bottom: float
    start_index: int
    completed_index: int
    start_time: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern,
            "type": self.type,
            "top": self.top,
            "bottom": self.bottom,
            "startIndex": self.start_index,
            "startTime": self.start_time,
            "completedIndex": self.completed_index,
        }


def detect_zones(candles: list[Candle]) -> list[DetectedZone]:
    """Return all fresh zones found in the supplied ascending candle list."""
    if len(candles) < 3:
        return []
    bodies = [_body(candle) for candle in candles]
    averages = _average_bodies(bodies)
    ranges = [_range(candle) for candle in candles]
    true_ranges = [_true_range(candles, index) for index in range(len(candles))]
    atrs = [_atr(true_ranges, index) for index in range(len(true_ranges))]
    strengths = [
        _candle_strength(candles[index], bodies[index], averages[index], true_ranges[index], atrs[index])
        for index in range(len(candles))
    ]
    zones: list[DetectedZone] = []
    for i in range(len(candles) - 2):
        zones.extend(_zones_from_initial(candles, i, strengths, atrs, true_ranges))
    return zones


def select_nearest(zones: list[DetectedZone], latest_close: float) -> list[DetectedZone]:
    """Keep the nearest fresh demand and supply zone to the latest close."""
    nearest_demand = _nearest_by_type(zones, DEMAND_PATTERNS, latest_close)
    nearest_supply = _nearest_by_type(zones, SUPPLY_PATTERNS, latest_close)
    return [zone for zone in (nearest_demand, nearest_supply) if zone is not None]


def _body(candle: Candle) -> float:
    return abs(candle.close - candle.open)


def _range(candle: Candle) -> float:
    return candle.high - candle.low


def _true_range(candles: list[Candle], index: int) -> float:
    candle = candles[index]
    if index == 0:
        return candle.high - candle.low
    previous_close = candles[index - 1].close
    return max(
        candle.high - candle.low,
        abs(candle.high - previous_close),
        abs(candle.low - previous_close),
    )


def _atr(ranges: list[float], index: int, period: int = 14) -> float:
    previous = ranges[max(0, index - period):index]
    if not previous:
        return ranges[index] if index < len(ranges) else 0.0
    return sum(previous) / len(previous)


def _candle_strength(candle: Candle, body: float, average_body: float, true_range: float, atr: float) -> tuple[bool, int]:
    candle_range = _range(candle)
    if candle_range <= 0 or true_range <= 0:
        return False, 0
    meets_body_average = body >= 1.2 * average_body if average_body > 0 else True
    body_to_range = body / candle_range
    size_strong = body_to_range >= 0.4 and (true_range >= 1.5 * atr if atr > 0 else True)
    ratio_strong = body_to_range >= 0.5 and meets_body_average and (true_range >= atr if atr == true_range else true_range >= 1.2 * atr)
    high_ratio_strong = body_to_range >= 0.85
    if not (size_strong or ratio_strong or high_ratio_strong):
        return False, 0
    if candle.close > candle.open:
        return True, 1
    if candle.close < candle.open:
        return True, -1
    return False, 0


def _is_base(candle: Candle, atr: float) -> bool:
    candle_range = _range(candle)
    if candle_range <= 0:
        return False
    return _body(candle) / candle_range < BASE_BODY_TO_RANGE


def _average_bodies(bodies: list[float]) -> list[float]:
    averages = []
    for i in range(len(bodies)):
        start = max(0, i - AVERAGE_BODY_WINDOW)
        previous = bodies[start:i]
        averages.append(sum(previous) / len(previous) if previous else 0.0)
    return averages


def _zones_from_initial(candles: list[Candle], i: int, strengths: list[tuple[bool, int]], atrs: list[float], true_ranges: list[float]) -> list[DetectedZone]:
    initial_is_strong, initial_direction = strengths[i]
    if not initial_is_strong:
        return []
    zones = []
    for base_count in range(1, MAX_BASE_CANDLES + 1):
        zone = _candidate_from_base_count(candles, i, base_count, initial_direction, strengths, atrs, true_ranges)
        if zone is not None:
            zones.append(zone)
    return zones


def _candidate_from_base_count(
    candles: list[Candle],
    initial_index: int,
    base_count: int,
    initial_direction: int,
    strengths: list[tuple[bool, int]],
    atrs: list[float],
    true_ranges: list[float],
) -> DetectedZone | None:
    base_start = initial_index + 1
    base_end = base_start + base_count - 1
    completed_index = base_end + 1
    if completed_index >= len(candles):
        return None
    if not all(_is_base(candles[index], atrs[index]) for index in range(base_start, base_end + 1)):
        return None
    final_is_strong, final_direction = strengths[completed_index]
    if not final_is_strong:
        return None
    pattern = _pattern(initial_direction, final_direction)
    if pattern is None:
        return None
    bottom, top = _bounds(pattern, candles[base_start:base_end + 1])
    zone_height = top - bottom
    completed_range = true_ranges[completed_index]
    atr = atrs[completed_index]
    if zone_height <= 0 or zone_height > 3.0 * atr or completed_range < 1.0 * zone_height:
        return None
    if not _is_fresh(candles, completed_index + 1, bottom, top):
        return None
    return DetectedZone(
        pattern=pattern,
        type="demand" if pattern in DEMAND_PATTERNS else "supply",
        top=top,
        bottom=bottom,
        start_index=base_start,
        completed_index=completed_index,
        start_time=candles[base_start].time,
    )


def _pattern(initial_direction: int, final_direction: int) -> str | None:
    if initial_direction == 1 and final_direction == 1:
        return "RBR"
    if initial_direction == -1 and final_direction == 1:
        return "DBR"
    if initial_direction == 1 and final_direction == -1:
        return "RBD"
    if initial_direction == -1 and final_direction == -1:
        return "DBD"
    return None


def _bounds(pattern: str, bases: list[Candle]) -> tuple[float, float]:
    body_tops = [max(candle.open, candle.close) for candle in bases]
    body_bottoms = [min(candle.open, candle.close) for candle in bases]
    if pattern in DEMAND_PATTERNS:
        return min(candle.low for candle in bases), max(body_tops)
    return min(body_bottoms), max(candle.high for candle in bases)


def _is_fresh(candles: list[Candle], start: int, bottom: float, top: float) -> bool:
    for candle in candles[start:]:
        if candle.high >= bottom and candle.low <= top:
            return False
    return True


def _nearest_by_type(zones: list[DetectedZone], patterns: frozenset[str], latest_close: float) -> DetectedZone | None:
    candidates = [zone for zone in zones if zone.pattern in patterns]
    if not candidates:
        return None
    return min(candidates, key=lambda zone: (_distance(zone, latest_close), -zone.completed_index))


def _distance(zone: DetectedZone, price: float) -> float:
    if zone.bottom <= price <= zone.top:
        return 0.0
    return min(abs(price - zone.bottom), abs(price - zone.top))
