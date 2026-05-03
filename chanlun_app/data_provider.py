from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BASE_DIR, LEVELS, STOCK_CACHE_FILE


class DataProviderError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class StockRecord:
    ts_code: str
    symbol: str
    name: str
    area: str = ""
    industry: str = ""
    market: str = ""
    exchange: str = ""
    list_date: str = ""
    cnspell: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "ts_code": self.ts_code,
            "symbol": self.symbol,
            "name": self.name,
            "area": self.area,
            "industry": self.industry,
            "market": self.market,
            "exchange": self.exchange,
            "list_date": self.list_date,
            "cnspell": self.cnspell,
        }


class TushareClient:
    def __init__(
        self,
        token: str | None = None,
        stock_cache_file: Path = STOCK_CACHE_FILE,
        cache_ttl_seconds: int = 24 * 60 * 60,
    ):
        self.token = token or _env_value("TUSHARE_TOKEN")
        self.stock_cache_file = stock_cache_file
        self.cache_ttl_seconds = cache_ttl_seconds
        self._pro: Any | None = None

    def _client(self) -> Any:
        if not self.token:
            raise DataProviderError("缺少 TUSHARE_TOKEN 环境变量，请先配置 Tushare Pro Token。", 500)
        if self._pro is None:
            try:
                import tushare as ts
            except ImportError as exc:
                raise DataProviderError("未安装 tushare，请先运行 pip install -r requirements.txt。", 500) from exc
            ts.set_token(self.token)
            self._pro = ts.pro_api()
        return self._pro

    def _read_stock_cache(self) -> pd.DataFrame | None:
        if not self.stock_cache_file.exists():
            return None
        age = time.time() - self.stock_cache_file.stat().st_mtime
        if age > self.cache_ttl_seconds:
            return None
        return pd.read_csv(self.stock_cache_file, dtype=str).fillna("")

    def load_stocks(self, force_refresh: bool = False) -> pd.DataFrame:
        cached = None if force_refresh else self._read_stock_cache()
        if cached is not None:
            return cached

        pro = self._client()
        fields = "ts_code,symbol,name,area,industry,market,exchange,list_date,cnspell"
        try:
            df = pro.stock_basic(exchange="", list_status="L", fields=fields)
        except Exception as exc:
            raise DataProviderError(f"Tushare 股票列表获取失败：{exc}", 502) from exc

        if df is None or df.empty:
            raise DataProviderError("Tushare 未返回股票列表数据。", 502)

        df = df.fillna("")
        self.stock_cache_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.stock_cache_file, index=False)
        return df

    def search_stocks(self, query: str, limit: int = 20) -> list[dict[str, str]]:
        q = (query or "").strip()
        if not q:
            return []

        df = self.load_stocks()
        q_upper = q.upper()
        q_lower = q.lower()

        symbol = df["symbol"].astype(str)
        ts_code = df["ts_code"].astype(str).str.upper()
        name = df["name"].astype(str)
        cnspell = df.get("cnspell", pd.Series([""] * len(df))).astype(str)

        exact_mask = (
            symbol.eq(q)
            | ts_code.eq(q_upper)
            | name.eq(q)
            | cnspell.str.upper().eq(q_upper)
        )
        fuzzy_mask = (
            symbol.str.startswith(q)
            | ts_code.str.startswith(q_upper)
            | name.str.contains(q, case=False, regex=False)
            | cnspell.str.lower().str.contains(q_lower, regex=False)
        )

        result = pd.concat([df[exact_mask], df[fuzzy_mask & ~exact_mask]]).head(limit)
        return [StockRecord(**self._stock_kwargs(row)).as_dict() for _, row in result.iterrows()]

    def resolve_stock(self, value: str) -> StockRecord:
        query = (value or "").strip()
        if not query:
            raise DataProviderError("请输入股票名称或代码。", 400)

        matches = self.search_stocks(query, limit=5)
        if not matches:
            raise DataProviderError(f"未找到股票：{query}", 404)

        exact = [
            item
            for item in matches
            if query.upper() in {item["ts_code"].upper(), item["symbol"].upper()}
            or query == item["name"]
        ]
        chosen = exact[0] if exact else matches[0]
        return StockRecord(**self._stock_kwargs(chosen))

    def get_klines(
        self,
        ts_code: str,
        level: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        if level not in LEVELS:
            raise DataProviderError(f"level 只支持 {_supported_levels_text()}。", 400)

        config = LEVELS[level]
        pro = self._client()
        if config.get("intraday"):
            return self._get_intraday_klines(pro, ts_code, level, start_date, end_date)

        api_name = config["api"]
        fields = "ts_code,trade_date,open,high,low,close,vol,amount"
        try:
            df = getattr(pro, api_name)(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields=fields,
            )
        except Exception as exc:
            raise DataProviderError(f"Tushare K线数据获取失败：{exc}", 502) from exc

        if df is None or df.empty:
            raise DataProviderError("没有获取到 K 线数据，请检查股票代码、日期范围或 Tushare 权限。", 404)

        return _standardize_kline_rows(df, ts_code, "trade_date")

    def _get_intraday_klines(
        self,
        pro: Any,
        ts_code: str,
        level: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        freq = LEVELS[level]["freq"]
        try:
            df = pro.stk_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=_minute_datetime(start_date, is_end=False),
                end_date=_minute_datetime(end_date, is_end=True),
            )
        except Exception as exc:
            raise DataProviderError(f"Tushare 分钟K线数据获取失败：{exc}", 502) from exc

        if df is None or df.empty:
            raise DataProviderError("没有获取到分钟 K 线数据，请检查股票代码、日期范围或 Tushare 分钟权限。", 404)

        return _standardize_kline_rows(df, ts_code, "trade_time")

    @staticmethod
    def _stock_kwargs(row: Any) -> dict[str, str]:
        getter = row.get if hasattr(row, "get") else row.__getitem__
        return {
            "ts_code": str(getter("ts_code", "")),
            "symbol": str(getter("symbol", "")),
            "name": str(getter("name", "")),
            "area": str(getter("area", "")),
            "industry": str(getter("industry", "")),
            "market": str(getter("market", "")),
            "exchange": str(getter("exchange", "")),
            "list_date": str(getter("list_date", "")),
            "cnspell": str(getter("cnspell", "")),
        }


def _standardize_kline_rows(df: pd.DataFrame, ts_code: str, date_column: str) -> list[dict[str, Any]]:
    if date_column not in df.columns:
        raise DataProviderError(f"Tushare 返回数据缺少 {date_column} 字段。", 502)

    df = df.fillna(0).sort_values(date_column).reset_index(drop=True)
    missing_columns = [column for column in ("open", "high", "low", "close") if column not in df.columns]
    if missing_columns:
        raise DataProviderError(f"Tushare 返回数据缺少字段：{', '.join(missing_columns)}。", 502)

    ts_codes = df["ts_code"] if "ts_code" in df.columns else pd.Series([ts_code] * len(df))
    vol = df["vol"] if "vol" in df.columns else pd.Series([0] * len(df))
    amount = df["amount"] if "amount" in df.columns else pd.Series([0] * len(df))

    rows: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        rows.append(
            {
                "index": int(idx),
                "ts_code": str(ts_codes.iloc[idx] or ts_code),
                "date": _compact_datetime(row[date_column]) if date_column == "trade_time" else str(row[date_column]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "vol": float(vol.iloc[idx] or 0),
                "amount": float(amount.iloc[idx] or 0),
            }
        )
    return rows


def _compact_datetime(value: Any) -> str:
    text = str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 12:
        return digits[:12]
    if len(digits) >= 8:
        return digits[:8]
    return text


def _minute_datetime(value: str, is_end: bool) -> str:
    day = f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return f"{day} {'23:59:59' if is_end else '00:00:00'}"


def _supported_levels_text() -> str:
    return "、".join(LEVELS)


def _env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value

    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")
    return None
