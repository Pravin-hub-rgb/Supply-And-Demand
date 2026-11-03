"""Unit tests for the Nifty 50 seed builder."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "build_nifty50_seed.py"
spec = importlib.util.spec_from_file_location("build_nifty50_seed", SCRIPT_PATH)
seed_builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(seed_builder)

NSE_CSV = """Company Name,Industry,Symbol,Series,ISIN Code
Example One Ltd.,Tech,ONE,EQ,INE000000001
Example Two Ltd.,Banking,TWO,EQ,INE000000002
"""

UPSTOX_CSV = """instrument_key,exchange_token,tradingsymbol,name,last_price,expiry,strike,tick_size,lot_size,instrument_type,option_type,exchange
NSE_EQ|INE000000001,1,ONE,EXAMPLE ONE,10.0,,,0.01,1,EQUITY,,NSE_EQ
BSE_EQ|INE000000001,2,ONE,EXAMPLE ONE,10.0,,,0.01,1,EQUITY,,BSE_EQ
NSE_EQ|INE000000002,3,TWO,EXAMPLE TWO,20.0,,,0.01,1,EQUITY,,NSE_EQ
NSE_EQ|INE000000002-BOND,4,TWOBOND,EXAMPLE TWO BOND,20.0,,,0.01,1,BOND,,NSE_EQ
"""


def test_build_seed_success():
    seed = seed_builder.build_seed(NSE_CSV, UPSTOX_CSV, expected_count=2)

    assert seed["index"] == "NIFTY 50"
    assert [row["symbol"] for row in seed["constituents"]] == ["ONE", "TWO"]
    assert [row["instrument_key"] for row in seed["constituents"]] == [
        "NSE_EQ|INE000000001",
        "NSE_EQ|INE000000002",
    ]


def test_build_seed_rejects_wrong_count():
    with pytest.raises(ValueError, match="Expected 1 Nifty 50 constituents"):
        seed_builder.build_seed(NSE_CSV, UPSTOX_CSV, expected_count=1)


def test_build_seed_rejects_missing_upstox_key():
    upstox_csv = UPSTOX_CSV.replace("NSE_EQ|INE000000002,3", "NSE_EQ|INE000000099,3")

    with pytest.raises(ValueError, match="Missing Upstox NSE_EQ keys for: TWO"):
        seed_builder.build_seed(NSE_CSV, upstox_csv, expected_count=2)


def test_parse_nse_csv_rejects_missing_columns():
    with pytest.raises(ValueError, match="missing columns"):
        seed_builder.parse_nse_csv("Company Name,Symbol\nExample,ONE\n")
