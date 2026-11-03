# Changelog

All notable user-visible changes are recorded here.

## 0.3.0 - 2026-11-03

- Added the Next.js frontend for phase 1 charts at `/charts`: Nifty 50 sidebar, search, timeframe switch, and candlestick rendering through `lightweight-charts`.
- Added frontend setup/build commands to the README and runbook.
- Excluded the local reference PDF from git; source/docs/config remain committed.

## 0.2.0 - 2026-11-03

- Added the FastAPI backend package with local SQLite cache and health/instruments/candles endpoints.
- Added a rate-aware Upstox downloader that round-robins `UPSTOX_ACCESS_TOKEN` and optional `UPSTOX_ACCESS_TOKEN_2..N`, with per-token pacing, 429 cooldowns, and 401 dead-token handling.
- Built the initial local candle cache: 24,700 daily, 5,300 weekly, and 12,424 monthly rows with no download failures.
- Added backend tests; suite currently passes with 20 tests.
- Documented Upstox raw `urllib` Cloudflare 403 block; backend uses `requests`.

## 0.1.0 - 2026-11-03

- Added project conventions, docs skeleton, local environment template, and initial Nifty 50 seed tooling.
- Defined phase 1 scope: Nifty 50 candlestick charts only; no scanner or live data yet.
- Defined history policy: Y/HY/Q/M use full available history from monthly candles; D/W use 2 years by default.
- Generated `config/nifty50.json` from official NSE constituent and Upstox instrument sources; all 50 instrument keys match ISINs.
- Verified Upstox historical candles around KOTAKBANK split and TRENT bonus ex-dates; candles are continuous, so no app-side corporate action adjustment is applied.
