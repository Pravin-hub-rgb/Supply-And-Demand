"""Project settings and secret loading for SupplynDemand."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_PATTERN = re.compile(r"^UPSTOX_ACCESS_TOKEN(?:_(\d+))?$")


@dataclass(frozen=True)
class DownloadSettings:
    pacing_seconds: float
    request_timeout_seconds: float
    retry_attempts: int
    initial_cooldown_seconds: float
    max_cooldown_seconds: float
    max_attempts_per_request: int


@dataclass(frozen=True)
class Settings:
    root: Path
    timeframes: list[str]
    database_path: Path
    seed_path: Path
    daily_history_years: int
    weekly_history_years: int
    download: DownloadSettings


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_settings(root: Path | None = None) -> Settings:
    """Load non-secret settings; raise RuntimeError with file context on failure."""
    root = root or repo_root()
    settings_path = root / "config" / "settings.json"
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
        data = raw["data"]
        app = raw["app"]
        download = raw["download"]
        return Settings(
            root=root,
            timeframes=list(app["timeframes"]),
            database_path=_resolve(root, data["databasePath"]),
            seed_path=_resolve(root, raw["seed"]["nifty50Path"]),
            daily_history_years=int(data["dailyHistoryYears"]),
            weekly_history_years=int(data["weeklyHistoryYears"]),
            download=DownloadSettings(
                pacing_seconds=float(download["pacingSeconds"]),
                request_timeout_seconds=float(download["requestTimeoutSeconds"]),
                retry_attempts=int(download["retryAttempts"]),
                initial_cooldown_seconds=float(download["initialCooldownSeconds"]),
                max_cooldown_seconds=float(download["maxCooldownSeconds"]),
                max_attempts_per_request=int(download["maxAttemptsPerRequest"]),
            ),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid settings file {settings_path}: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to read settings file {settings_path}: {exc}") from exc


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv-style file without logging values."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = _clean_env_value(value)
    return values


def load_upstox_tokens(root: Path | None = None) -> list[str]:
    """Return primary then numbered extra Upstox tokens; fail if none are usable."""
    root = root or repo_root()
    env = load_env_file(root / ".env.local")
    env.update({k: v for k, v in os.environ.items() if TOKEN_PATTERN.match(k)})
    numbered: list[tuple[int, str]] = []
    primary = ""
    for key, value in env.items():
        match = TOKEN_PATTERN.match(key)
        if not match or not value or len(value) <= 20:
            continue
        index = match.group(1)
        if index is None:
            primary = value
        else:
            numbered.append((int(index), value))
    ordered = ([primary] if primary else []) + [token for _, token in sorted(numbered)]
    if not ordered:
        raise RuntimeError("No Upstox access token found. Add UPSTOX_ACCESS_TOKEN to .env.local.")
    return ordered


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _clean_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
