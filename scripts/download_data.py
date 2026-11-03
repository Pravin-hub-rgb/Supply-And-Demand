"""Download Nifty 50 candles into the local SQLite cache."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from supplyndemand.config import load_settings, load_upstox_tokens
from supplyndemand.db import connect, migrate
from supplyndemand.downloader import download_seeded_symbols

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    """Parse args, run the download, and exit non-zero if anything failed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", action="append", help="Limit to one Nifty 50 symbol; repeat for multiple.")
    args = parser.parse_args()
    settings = load_settings(ROOT)
    tokens = load_upstox_tokens(ROOT)
    logger.info("Loaded %d Upstox token(s)", len(tokens))
    with connect(settings.database_path) as conn:
        migrate(conn)
        summary = download_seeded_symbols(conn, settings, tokens, symbols=args.symbol)
    logger.info("Downloaded candles D=%d W=%d M=%d", summary["downloaded"]["D"], summary["downloaded"]["W"], summary["downloaded"]["M"])
    if summary["failures"]:
        for failure in summary["failures"]:
            logger.error("Failure: %s", failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
