# SupplynDemand

A local web app for studying Nifty 50 supply and demand on higher timeframes.

Current status: **backend data pipeline implemented and cache built**. The frontend is not implemented yet.

Upstox historical candles are verified working with all configured tokens. Upstox candles are treated as already adjusted for split/bonus events based on KOTAKBANK and TRENT ex-date validation; the app will not apply a second adjustment.

## Goal

Phase 1 shows candlestick charts for current Nifty 50 constituents across:

- Yearly
- Half-yearly
- Quarterly
- Monthly
- Weekly
- Daily

History policy:

- Y / HY / Q / M: full history available from Upstox, derived from native monthly candles
- W / D: recent history, 2 years by default

Supply/demand zones, scanners, live data, and paper trading are intentionally out of scope for phase 1.

## Requirements

- Windows
- Python 3.10+
- Node.js 24+ and Bun 1.3+ (or npm) for the frontend
- An Upstox access token for historical candle downloads

## Layout

```
config/     Committed non-secret settings and seed data
docs/       Architecture, decisions, operations
scripts/    Data preparation tools, not app logic
tests/      All tests live here
backend/    FastAPI backend package and requirements
frontend/   Next.js frontend, added in a later step
data/       Runtime SQLite cache, git-ignored
```

## Setup

1. Copy the environment template if you need a fresh file:
   ```powershell
   Copy-Item .env.example .env.local
   ```

2. Paste Upstox tokens into `.env.local`:
   ```
   UPSTOX_ACCESS_TOKEN=...
   UPSTOX_ACCESS_TOKEN_2=...
   UPSTOX_ACCESS_TOKEN_3=...
   UPSTOX_ACCESS_TOKEN_4=...
   ```
   Extra tokens are optional. The downloader round-robins available tokens.

3. Create the Python virtual environment and install backend deps:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
   ```

4. Build or refresh the Nifty 50 seed if NSE constituents changed:
   ```powershell
   python scripts/build_nifty50_seed.py
   ```

5. Download/build the local candle cache:
   ```powershell
   .\.venv\Scripts\python.exe scripts/download_data.py
   ```
   Use `--symbol RELIANCE` to refresh one symbol. Failures are printed and make the script exit non-zero; successful candles are still upserted.

## Run the backend

```powershell
$env:PYTHONPATH = 'backend/src'
.\.venv\Scripts\python.exe -m uvicorn supplyndemand.main:app --app-dir backend/src --host 127.0.0.1 --port 8011
```

Check it:

```powershell
curl http://127.0.0.1:8011/api/health
curl "http://127.0.0.1:8011/api/candles/RELIANCE?timeframe=M"
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests/python
```

## Troubleshooting

- Historical downloads fail immediately: check `UPSTOX_ACCESS_TOKEN` in `.env.local`. Tokens expire; generate fresh ones when needed.
- `403 Cloudflare` from raw `urllib`: use `requests` (the backend does); do not spoof browser signatures.
- `429 rate limited`: the downloader marks that token as cooling and uses the others; wait for cooldown if all tokens are limited.
- Seed script cannot download NSE or Upstox data: check internet access and rerun; the script fails before writing partial output.
- Missing instrument key for a constituent: rerun the seed script and inspect the error; do not hand-edit `config/nifty50.json` unless you know the key is correct.

## Secrets

Never commit `.env.local`, Upstox tokens, or runtime data under `data/`.
