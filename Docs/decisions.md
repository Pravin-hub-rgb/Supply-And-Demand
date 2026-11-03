# Decisions

## 2026-11-03 - Build a new lean app instead of forking TradeStack or StocksSS

Options considered: fork TradeStack, fork StocksSS, or build a new lean app reusing their patterns.
Reason: the goal is a focused Nifty 50 S/D chart app. Forks would inherit unneeded complexity such as NSE-wide scanners, live trading paths, large databases, and mixed package managers.

## 2026-11-03 - Use Upstox historical candles as the price source of truth

Options considered: NSE bhavcopy plus resampling, Yahoo Finance, Upstox API.
Reason: user chose Upstox. Upstox V3 provides native daily, weekly, and monthly candles from Jan 2000; daily is limited to one decade per request, weekly/monthly have no documented limit.
Validation: RELIANCE monthly history returned 323 candles from 2000-01-01 with HTTP 200. Kotak Mahindra Bank split on 2026-01-14 (5 to 1 face value) and Trent bonus on 2026-06-04 (1:2) both show continuous candles around ex-dates, so Upstox historical candles are treated as already corporate-action adjusted for those events. Do not apply a second adjustment in the app.

## 2026-11-03 - Derive Y/HY/Q from monthly candles

Options considered: resample everything from daily, fetch native W/M and derive higher timeframes.
Reason: monthly is the highest native timeframe. Quarterly, half-yearly, and yearly are calendar aggregations. Daily and weekly remain native API calls because they need finer granularity.

## 2026-11-03 - Limit D/W history to 2 years by default

Reason: user requested long history only for higher timeframes; daily/weekly are for recent context and faster downloads. Stored in `config/settings.json` as `dailyHistoryYears` and `weeklyHistoryYears`.

## 2026-11-03 - Keep Nifty 50 universe as a committed snapshot

Reason: user chose current snapshot over automatic quarterly refresh. `scripts/build_nifty50_seed.py` refreshes the seed from official NSE and Upstox sources when index constituents change.

## 2026-11-03 - Do not double-adjust Upstox candles

Reason: Upstox validation on KOTAKBANK and TRENT showed continuous candles across split/bonus ex-dates, which would be impossible if those candles were raw. The app stores/serves Upstox candles unchanged. Adjustment may be revisited only if Upstox documents otherwise or repeated ex-dates show artificial gaps.

## 2026-11-03 - Use requests, not raw urllib, for Upstox

Options considered: raw `urllib`, browser-signature spoofing, `requests`, official SDK.
Reason: raw `urllib` received Cloudflare 403 "browser_signature_banned". The project uses plain `requests` with Authorization/Accept headers like the existing StocksSS client; no browser spoofing or auth bypass.

## 2026-11-03 - Multi-token rate-aware downloader

Options considered: single token with fixed sleeps, StocksSS-style worker pool, sequential round-robin pool.
Reason: StocksSS proved per-token pacing and 429 cooldowns are needed for large Upstox downloads. The lean app uses a synchronous round-robin pool: `UPSTOX_ACCESS_TOKEN` plus optional `_2..N`, ~0.3s pacing per token, exponential cooldown on 429, dead-token handling on 401, and no token values in logs. It avoids copying StocksSS's 16GB DB/janitor complexity because this app only downloads 50 symbols.

## 2026-11-03 - Replace only recent D/W windows

Reason: D/W are limited to 2 years by policy. The downloader deletes D/W candles older than the configured window before reinsert, so changing `dailyHistoryYears` or `weeklyHistoryYears` does not leave stale older rows. Monthly full history is upserted and retained.

## 2026-11-03 - Frontend stays client-side and leans on lightweight-charts

Options considered: server-side data fetching with Next.js route handlers, a full-stack framework, or a client-side Next.js UI calling FastAPI directly.
Reason: the app is local single-user. Client-side fetching keeps the backend responsible for market data and SQLite access, avoids duplicating business logic in Next.js, and matches the simple browser/API split. `lightweight-charts` is already used in the user's other projects and is enough for candlesticks without MUI/Tailwind/chart bloat.

## 2026-11-03 - Exclude copyrighted reference PDFs from git

Options considered: commit the supplied PDF, gitignore the exact file, or keep it elsewhere.
Reason: the PDF looks like paid course material and is not needed for the app to build or run. The exact file is gitignored; code and docs remain committed.

## 2026-11-03 - No auth in phase 1

Reason: local single-user tool. Bind backend and CORS to localhost only. Add auth only if exposure beyond localhost is ever needed.
