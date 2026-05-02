from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
STOCK_CACHE_FILE = CACHE_DIR / "stocks.csv"

LEVELS = {
    "daily": {"label": "日线", "api": "daily", "default_days": 365 * 3},
    "weekly": {"label": "周线", "api": "weekly", "default_days": 365 * 8},
    "monthly": {"label": "月线", "api": "monthly", "default_days": 365 * 15},
}


def default_date_range(level: str) -> tuple[str, str]:
    config = LEVELS.get(level, LEVELS["daily"])
    end = date.today()
    start = end - timedelta(days=config["default_days"])
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def normalize_yyyymmdd(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().replace("-", "").replace("/", "")
    return cleaned if len(cleaned) == 8 and cleaned.isdigit() else None
