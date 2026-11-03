# Runbook

## Logs

Logs are currently written to stdout/stderr by the CLI and backend process. Rotating file logs under `data/logs/` are not implemented yet.

## Common tasks

### Refresh Nifty 50 seed

```powershell
python scripts/build_nifty50_seed.py
```

Expected result: `config/nifty50.json` contains 50 constituents with non-empty instrument keys.

Failure modes:

- NSE CSV download fails: rerun with network access; script exits before writing `config/nifty50.json`.
- Upstox instrument master download fails: rerun; script exits before writing seed.
- Any constituent missing an NSE_EQ instrument key: script exits with the missing symbols; verify symbol validity on NSE/Upstox before proceeding.

### Build or refresh the candle cache

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py
.\.venv\Scripts\python.exe scripts/download_data.py --symbol RELIANCE
```

Behavior:

- Monthly candles: full Upstox history from 2000, upserted.
- Daily/weekly candles: last 2 years by default; older D/W rows are deleted before reinsert.
- Tokens: `UPSTOX_ACCESS_TOKEN` plus optional `UPSTOX_ACCESS_TOKEN_2..N`. Tokens are round-robined; `429` cools down that token exponentially; `401` marks it dead.
- Failures are listed and make the command exit non-zero. Partial successful candles are kept.

### Run the backend API

```powershell
$env:PYTHONPATH = 'backend/src'
.\.venv\Scripts\python.exe -m uvicorn supplyndemand.main:app --app-dir backend/src --host 127.0.0.1 --port 8011
```

Health check:

```powershell
curl http://127.0.0.1:8011/api/health
```

### Run the frontend

In another terminal:

```powershell
Set-Location frontend
bun run dev
```

Open `http://localhost:3005/charts`. The frontend reads `NEXT_PUBLIC_API_BASE` if set, otherwise defaults to `http://127.0.0.1:8011`.

### Upstox token expired

Generate a fresh token and paste it into `.env.local`. Do not commit or share it. Remove or replace dead `UPSTOX_ACCESS_TOKEN*` entries; the downloader will treat `401` tokens as dead for that run.

## Verification

Backend test command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/python
```

Frontend verification command:

```powershell
Set-Location frontend
bun run build
Set-Location ..
```

Last verified: backend suite 20 passed; frontend production build succeeded. Browser chart checks for D/W/M/Q/HY/Y are still pending.
