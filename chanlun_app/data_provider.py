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
            raise DataProviderError("level 只支持 daily、weekly、monthly。", 400)

        pro = self._client()
        api_name = LEVELS[level]["api"]
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

        df = df.fillna(0).sort_values("trade_date").reset_index(drop=True)
        rows: list[dict[str, Any]] = []
        for idx, row in df.iterrows():
            rows.append(
                {
                    "index": int(idx),
                    "ts_code": str(row["ts_code"]),
                    "date": str(row["trade_date"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "vol": float(row.get("vol", 0)),
                    "amount": float(row.get("amount", 0)),
                }
            )
        return rows

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
