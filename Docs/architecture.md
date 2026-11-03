# Architecture

SupplynDemand is a local single-user study app for Nifty 50 supply and demand.

## Local run model

- Root `bun dev` runs `dev.js`, which spawns the backend uvicorn process and the frontend Next.js process with prefixed output.
- By default it does not kill processes using ports 3005/8011; it reports PIDs and exits. `bun dev -- --kill` is explicit opt-in for local cleanup.

## Phase 1 data flow

1. `scripts/build_nifty50_seed.py`
   - Downloads the current Nifty 50 constituent list from NSE.
   - Downloads the Upstox instrument master.
   - Writes `config/nifty50.json` with symbol, name, industry, ISIN, and instrument key.
2. `scripts/download_data.py` uses the backend package to download OHLCV candles from Upstox V3 historical candle API.
   - Validation on KOTAKBANK and TRENT showed split/bonus events do not create artificial candle gaps, so candles are used as-is.
   - Monthly history is full from 2000; daily/weekly are last 2 years by default.
   - Upstox tokens are loaded from `.env.local` as `UPSTOX_ACCESS_TOKEN` plus optional numbered tokens. Tokens are round-robined with per-token pacing and 429/401 handling.
3. Backend stores candles in SQLite.
4. Backend serves timeframes:
   - Native: D, W, M
   - Derived from monthly candles: Q, HY, Y
5. Next.js frontend renders candlestick charts with `lightweight-charts` at `/charts`.
   - `/` redirects to `/charts`.
   - Client-side fetching calls the backend directly with `NEXT_PUBLIC_API_BASE` or `http://127.0.0.1:8011`.

## Module boundaries

- `supplyndemand.config` loads non-secret settings and token names; values are never logged.
- `supplyndemand.db` owns SQLite connections and schema.
- `supplyndemand.upstox` fetches Upstox JSON and parses/validates candles.
- `supplyndemand.rate_limit` owns token round-robin, pacing, cooldowns, and dead-token detection.
- `supplyndemand.candles` owns parsing and calendar aggregation.
- `supplyndemand.repository` owns SQL reads/writes.
- `supplyndemand.zones` detects yearly supply/demand patterns and freshness.
- `frontend/src/lib/zoneRectangles.ts` renders detected yearly zones as chart rectangles.
- `supplyndemand.api` exposes local HTTP routes; business logic stays in modules.
- `frontend/src/lib/api.ts` is the browser API client with timeout-free fetch and explicit API errors.
- `frontend/src/components/CandleChart.tsx` owns chart creation/removal, resize handling, session-visible logical-range restore, and the OHLCV hover overlay.
- `frontend/src/lib/chartMemory.ts` stores per symbol+timeframe visible logical ranges plus a last-used fallback in page session state.
- `frontend/src/components/StockSidebar.tsx` and `TimeframeSwitch.tsx` own list and timeframe UI.
- Frontend renders UI and does not compute market data.

## Runtime storage

- `data/supplyndemand.db` holds the local cache.
- `data/` is git-ignored.
- `config/nifty50.json` is committed seed data.

## Not implemented yet

- Scanner / zones / live data
