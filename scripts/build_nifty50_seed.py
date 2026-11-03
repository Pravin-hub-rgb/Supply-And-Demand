"""Build config/nifty50.json from official NSE and Upstox instrument sources."""

from __future__ import annotations

import csv
import gzip
import io
import json
import logging
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

NSE_URL = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
UPSTOX_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "config" / "nifty50.json"
EXPECTED_CONSTITUENTS = 50
USER_AGENT = "SupplynDemandSeedBuilder/1.0"
REQUIRED_NSE_COLUMNS = {"Company Name", "Industry", "Symbol", "Series", "ISIN Code"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def fetch_text(url: str) -> str:
    """Download a UTF-8 text resource or raise RuntimeError with the URL context."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8-sig")
    except Exception as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc


def fetch_gzip_text(url: str) -> str:
    """Download a gzipped UTF-8 resource or raise RuntimeError with the URL context."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return gzip.decompress(response.read()).decode("utf-8-sig")
    except Exception as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc


def parse_nse_csv(text: str) -> list[dict[str, str]]:
    """Parse and validate the NSE Nifty 50 constituent CSV."""
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("NSE constituent CSV is empty")
    missing = REQUIRED_NSE_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"NSE constituent CSV missing columns: {sorted(missing)}")
    constituents = []
    for row in rows:
        if (row.get("Series") or "").strip() != "EQ":
            raise ValueError(f"Non-EQ series for {row.get('Symbol')}")
        constituents.append(
            {
                "symbol": (row.get("Symbol") or "").strip(),
                "name": (row.get("Company Name") or "").strip(),
                "industry": (row.get("Industry") or "").strip(),
                "isin": (row.get("ISIN Code") or "").strip(),
            }
        )
    return constituents


def parse_upstox_equity_keys(text: str) -> set[str]:
    """Return the set of NSE equity instrument keys from the Upstox instrument master."""
    rows = csv.DictReader(io.StringIO(text))
    keys = {
        row["instrument_key"]
        for row in rows
        if row.get("exchange") == "NSE_EQ" and row.get("instrument_type") == "EQUITY"
    }
    if not keys:
        raise ValueError("Upstox instrument master contained no NSE_EQ EQUITY rows")
    return keys


def build_seed(nse_csv: str, upstox_csv: str, expected_count: int = EXPECTED_CONSTITUENTS) -> dict[str, Any]:
    """Combine NSE constituents and Upstox instrument keys into one seed object."""
    constituents = parse_nse_csv(nse_csv)
    keys = parse_upstox_equity_keys(upstox_csv)
    if len(constituents) != expected_count:
        raise ValueError(f"Expected {expected_count} Nifty 50 constituents, got {len(constituents)}")
    missing = []
    for row in constituents:
        instrument_key = f"NSE_EQ|{row['isin']}"
        if instrument_key in keys:
            row["instrument_key"] = instrument_key
        else:
            missing.append(f"{row['symbol']} ({row['isin']})")
    if missing:
        raise ValueError(f"Missing Upstox NSE_EQ keys for: {', '.join(missing)}")
    return {
        "index": "NIFTY 50",
        "source": {"constituents": NSE_URL, "instrument_keys": UPSTOX_INSTRUMENTS_URL},
        "constituents": constituents,
    }


def write_seed(seed: dict[str, Any], path: Path = OUTPUT_PATH) -> None:
    """Atomically replace the seed file so a failed build leaves the old seed intact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as handle:
        json.dump(seed, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def main() -> int:
    """Download sources, validate them, and write config/nifty50.json."""
    try:
        seed = build_seed(fetch_text(NSE_URL), fetch_gzip_text(UPSTOX_INSTRUMENTS_URL))
        write_seed(seed, OUTPUT_PATH)
    except Exception as exc:
        logger.error("Failed to build Nifty 50 seed: %s", exc)
        return 1
    logger.info("Wrote %d constituents to %s", len(seed["constituents"]), OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
