from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BASE_DIR, LEVELS, STOCK_CACHE_FILE
from .hot_money_store import HotMoneyDailyTradeStore, HotMoneyStoreError
from .stock_basic_store import StockBasicCacheStore, StockBasicStoreError
from .system_config_store import (
    managed_config_value,
    mysql_dsn_from_env as _shared_mysql_dsn_from_env,
    raw_env_value as _shared_raw_env_value,
    safe_env_int as _shared_safe_env_int,
)


logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class BoardRecord:
    ts_code: str
    name: str
    source: str
    source_label: str
    idx_type: str
    type_key: str = ""
    trade_date: str = ""
    leading: str = ""
    leading_code: str = ""
    pct_change: str = ""
    leading_pct: str = ""
    total_mv: str = ""
    turnover_rate: str = ""
    up_num: str = ""
    down_num: str = ""
    level: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "ts_code": self.ts_code,
            "name": self.name,
            "source": self.source,
            "source_label": self.source_label,
            "idx_type": self.idx_type,
            "type_key": self.type_key,
            "trade_date": self.trade_date,
            "leading": self.leading,
            "leading_code": self.leading_code,
            "pct_change": self.pct_change,
            "leading_pct": self.leading_pct,
            "total_mv": self.total_mv,
            "turnover_rate": self.turnover_rate,
            "up_num": self.up_num,
            "down_num": self.down_num,
            "level": self.level,
        }


class TushareClient:
    REVIEW_INDEXES = (
        ("000001.SH", "上证综指"),
        ("399001.SZ", "深证成指"),
        ("399006.SZ", "创业板指"),
    )

    def __init__(
        self,
        token: str | None = None,
        stock_cache_file: Path = STOCK_CACHE_FILE,
        cache_ttl_seconds: int = 24 * 60 * 60,
        board_cache_ttl_seconds: int = 6 * 60 * 60,
        hot_money_store: HotMoneyDailyTradeStore | None = None,
        stock_basic_store: StockBasicCacheStore | None = None,
    ):
        self.token = token or managed_config_value("TUSHARE_TOKEN")
        self.stock_cache_file = stock_cache_file
        self.cache_ttl_seconds = cache_ttl_seconds
        self.board_cache_ttl_seconds = board_cache_ttl_seconds
        self._pro: Any | None = None
        self._board_cache: dict[str, tuple[float, pd.DataFrame]] = {}
        self._board_member_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
        self._hot_money_cache: tuple[float, list[dict[str, Any]]] | None = None
        self._hot_money_detail_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._hot_money_detail_cache_dir = BASE_DIR / "cache" / "hot_money_detail"
        mysql_dsn = _mysql_dsn_from_env()
        self._hot_money_store = hot_money_store or HotMoneyDailyTradeStore(
            dsn=mysql_dsn,
            min_size=_safe_env_int("MYSQL_POOL_MIN_SIZE", 1),
            max_size=_safe_env_int("MYSQL_POOL_MAX_SIZE", 4),
        )
        self._stock_basic_store = stock_basic_store or StockBasicCacheStore(
            dsn=mysql_dsn,
            min_size=_safe_env_int("MYSQL_POOL_MIN_SIZE", 1),
            max_size=_safe_env_int("MYSQL_POOL_MAX_SIZE", 4),
        )

    def _client(self) -> Any:
        if not self.token:
            raise DataProviderError("缺少 TUSHARE_TOKEN 环境变量，请先配置 Tushare Pro Token。", 500)
        if self._pro is None:
            try:
                import tushare as ts
            except ImportError as exc:
                raise DataProviderError("未安装 tushare，请先运行 pip install -r requirements.txt。", 500) from exc
            self._pro = ts.pro_api(self.token)
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

    def search_eastmoney_boards(self, query: str, board_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        return self.search_boards("dc", query=query, board_type=board_type, limit=limit)

    def load_eastmoney_boards(self, board_type: str = "", force_refresh: bool = False) -> pd.DataFrame:
        return self.load_boards("dc", board_type=board_type, force_refresh=force_refresh)

    def get_eastmoney_board_members(
        self,
        ts_code: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict[str, str]]:
        return self.get_board_members("dc", ts_code=ts_code, trade_date=trade_date, force_refresh=force_refresh)

    def search_tdx_boards(self, query: str, board_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        return self.search_boards("tdx", query=query, board_type=board_type, limit=limit)

    def search_ths_boards(self, query: str, board_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        return self.search_boards("ths", query=query, board_type=board_type, limit=limit)

    def search_boards(self, source: str, query: str, board_type: str = "", limit: int = 20) -> list[dict[str, str]]:
        q = (query or "").strip()
        if not q:
            return []

        df = self.load_boards(source=source, board_type=board_type)
        if df.empty:
            return []

        q_upper = q.upper()
        q_lower = q.lower()
        ts_code = df["ts_code"].astype(str).str.upper()
        name = df["name"].astype(str)
        leading = df.get("leading", pd.Series([""] * len(df))).astype(str)

        exact_mask = ts_code.eq(q_upper) | name.eq(q)
        fuzzy_mask = (
            ts_code.str.startswith(q_upper)
            | name.str.contains(q, case=False, regex=False)
            | leading.str.lower().str.contains(q_lower, regex=False)
        )
        result = pd.concat([df[exact_mask], df[fuzzy_mask & ~exact_mask]]).head(limit)
        return [BoardRecord(**self._board_kwargs(row, source=source)).as_dict() for _, row in result.iterrows()]

    def load_boards(self, source: str, board_type: str = "", force_refresh: bool = False) -> pd.DataFrame:
        config = _board_source_config(source)
        normalized = _normalize_board_type(source, board_type)
        cache_key = f"{source}:{normalized or '__all__'}"
        cached = None if force_refresh else self._read_board_cache(cache_key)
        if cached is not None:
            return cached

        frames: list[pd.DataFrame] = []
        types = [normalized] if normalized else list(config["types"].values())
        for idx_type in types:
            frame = self._fetch_board_snapshot(source, idx_type)
            if frame is not None and not frame.empty:
                frames.append(frame)

        if not frames:
            raise DataProviderError(f"Tushare 未返回{config['label']}列表，请检查接口权限或稍后重试。", 502)

        df = pd.concat(frames, ignore_index=True).fillna("")
        for column in ("ts_code", "name", "idx_type"):
            if column not in df.columns:
                df[column] = ""
        df = (
            df.drop_duplicates(subset=["ts_code"])
            .sort_values(["idx_type", "name"])
            .reset_index(drop=True)
        )
        self._board_cache[cache_key] = (time.time(), df)
        return df

    def get_board_members(
        self,
        source: str,
        ts_code: str,
        trade_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict[str, str]]:
        cleaned_code = (ts_code or "").strip().upper()
        if not cleaned_code:
            raise DataProviderError("缺少板块代码。", 400)

        config = _board_source_config(source)
        cache_key = f"{source}:{cleaned_code}:{trade_date or 'latest'}"
        cached = None if force_refresh else self._read_board_member_cache(cache_key)
        if cached is not None:
            return cached

        pro = self._client()
        fields = config["member_fields"]
        api_name = config["member_api"]
        for day in _recent_trade_dates(12, preferred=trade_date):
            try:
                df = getattr(pro, api_name)(ts_code=cleaned_code, trade_date=day, fields=fields)
            except Exception as exc:
                raise DataProviderError(_friendly_tushare_board_error(config["label"], "成分获取失败", exc), 502) from exc
            if df is not None and not df.empty:
                members = self._standardize_board_members(df, source=source)
                self._board_member_cache[cache_key] = (time.time(), members)
                return members

        try:
            df = getattr(pro, api_name)(ts_code=cleaned_code, fields=fields)
        except Exception as exc:
            raise DataProviderError(_friendly_tushare_board_error(config["label"], "成分获取失败", exc), 502) from exc
        if df is None or df.empty:
            raise DataProviderError(f"未获取到{config['label']} {cleaned_code} 的成分股。", 404)

        members = self._standardize_board_members(df, source=source)
        self._board_member_cache[cache_key] = (time.time(), members)
        return members

    def get_stock_dc_concepts(
        self,
        ts_code: str,
        trade_date: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, str]]:
        cleaned_code = (ts_code or "").strip().upper()
        if not cleaned_code:
            raise DataProviderError("缺少股票代码。", 400)

        pro = self._client()
        fields = "ts_code,trade_date,name,theme_code,industry_code,industry,reason,hot_num"
        df = None
        for day in _recent_trade_dates(12, preferred=trade_date):
            try:
                df = pro.dc_concept_cons(ts_code=cleaned_code, trade_date=day, fields=fields)
            except Exception as exc:
                raise DataProviderError(_friendly_tushare_market_error("东方财富题材成分", exc), 502) from exc
            if df is not None and not df.empty:
                break

        if df is None or df.empty:
            try:
                df = pro.dc_concept_cons(ts_code=cleaned_code, fields=fields)
            except Exception as exc:
                raise DataProviderError(_friendly_tushare_market_error("东方财富题材成分", exc), 502) from exc

        if df is None or df.empty:
            return []

        concept_snapshot = self.load_boards("dc", board_type="concept")
        concept_name_map = {
            str(row["ts_code"]).upper(): str(row["name"])
            for _, row in concept_snapshot.iterrows()
            if str(row.get("ts_code", "")).strip()
        }

        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in df.fillna("").sort_values(by=["trade_date", "hot_num"], ascending=[False, True]).to_dict("records"):
            theme_code = str(row.get("theme_code", "")).strip().upper()
            if not theme_code or theme_code in seen:
                continue
            seen.add(theme_code)
            normalized.append(
                {
                    "theme_code": theme_code,
                    "theme_name": concept_name_map.get(theme_code, theme_code),
                    "trade_date": str(row.get("trade_date", "")).strip(),
                    "industry": str(row.get("industry", "")).strip(),
                    "reason": str(row.get("reason", "")).strip(),
                    "hot_num": str(row.get("hot_num", "")).strip(),
                }
            )
            if len(normalized) >= limit:
                break
        return normalized

    def get_stock_bak_basic(
        self,
        ts_code: str,
        trade_date: str | None = None,
    ) -> dict[str, Any]:
        cleaned_code = (ts_code or "").strip().upper()
        if not cleaned_code:
            raise DataProviderError("缺少股票代码。", 400)

        cached = self._read_stock_basic_store_cache(cleaned_code, trade_date)
        if cached:
            return cached

        pro = self._client()
        fields = (
            "trade_date,ts_code,name,industry,area,pe,pb,float_share,total_share,"
            "list_date,rev_yoy,profit_yoy,gpr,npr,holder_num"
        )
        df = None
        for day in _recent_trade_dates(20, preferred=trade_date):
            try:
                df = pro.bak_basic(ts_code=cleaned_code, trade_date=day, fields=fields)
            except Exception as exc:
                raise DataProviderError(_friendly_tushare_market_error("备用基础资料", exc), 502) from exc
            if df is not None and not df.empty:
                break

        if df is None or df.empty:
            try:
                df = pro.bak_basic(ts_code=cleaned_code, fields=fields)
            except Exception as exc:
                raise DataProviderError(_friendly_tushare_market_error("备用基础资料", exc), 502) from exc

        if df is None or df.empty:
            return {}

        row = df.fillna("").sort_values(by=["trade_date"], ascending=False).iloc[0].to_dict()
        normalized = {str(key): _json_safe_scalar(value) for key, value in row.items()}
        self._write_stock_basic_store_cache({"ts_code": cleaned_code}, normalized)
        return normalized

    def save_stock_basic_cache(
        self,
        stock: dict[str, Any],
        bak_basic: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stock_payload = dict(stock or {})
        ts_code = str(stock_payload.get("ts_code") or "").strip().upper()
        if not ts_code:
            raise DataProviderError("缺少股票代码，无法写入基础资料缓存。", 400)

        if not self._stock_basic_store.enabled:
            return {
                "status": "disabled",
                "message": "未配置 MySQL 缓存连接，已跳过基础资料缓存。",
                "ts_code": ts_code,
            }

        basics = dict(bak_basic or {})
        if not basics:
            basics = self.get_stock_bak_basic(ts_code)
        if not basics:
            return {
                "status": "empty",
                "message": "当前没有可写入的基础资料快照。",
                "ts_code": ts_code,
            }

        self._write_stock_basic_store_cache(stock_payload, basics)
        return {
            "status": "ok",
            "message": "股票基础资料已写入 MySQL 缓存。",
            "ts_code": ts_code,
            "trade_date": str(basics.get("trade_date") or ""),
        }

    def get_market_indices(self, trade_date: str | None = None) -> dict[str, Any]:
        pro = self._client()
        daily_fields = "ts_code,trade_date,close,open,high,low,pre_close,change,pct_chg,vol,amount"
        basic_fields = "ts_code,trade_date,turnover_rate,pe,pb"
        items: list[dict[str, Any]] = []
        actual_trade_date = ""

        for ts_code, name in self.REVIEW_INDEXES:
            row = None
            for day in _trade_date_candidates(trade_date, 8):
                try:
                    df = pro.index_daily(ts_code=ts_code, trade_date=day, fields=daily_fields)
                except Exception as exc:
                    raise DataProviderError(_friendly_tushare_market_error("大盘指数行情", exc), 502) from exc
                if df is not None and not df.empty:
                    row = df.fillna("").sort_values(by=["trade_date"], ascending=False).iloc[0].to_dict()
                    actual_trade_date = str(row.get("trade_date", "") or actual_trade_date)
                    break
            if row is None:
                continue

            basic_row: dict[str, Any] = {}
            try:
                basic_df = pro.index_dailybasic(
                    ts_code=ts_code,
                    trade_date=str(row.get("trade_date", "")).strip(),
                    fields=basic_fields,
                )
                if basic_df is not None and not basic_df.empty:
                    basic_row = basic_df.fillna("").sort_values(by=["trade_date"], ascending=False).iloc[0].to_dict()
            except Exception:
                basic_row = {}

            merged = {str(key): _json_safe_scalar(value) for key, value in row.items()}
            merged.update({str(key): _json_safe_scalar(value) for key, value in basic_row.items()})
            merged["name"] = name
            items.append(merged)

        return {"trade_date": actual_trade_date or (trade_date or ""), "items": items}

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

        try:
            import tushare as ts
        except ImportError as exc:
            raise DataProviderError("未安装 tushare，请先运行 pip install -r requirements.txt。", 500) from exc

        try:
            df = ts.pro_bar(
                api=pro,
                ts_code=ts_code,
                adj="qfq",
                freq=config["freq"],
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            raise DataProviderError(f"Tushare 前复权K线数据获取失败：{exc}", 502) from exc

        if df is None or df.empty:
            raise DataProviderError("没有获取到前复权 K 线数据，请检查股票代码、日期范围或 Tushare 权限。", 404)

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

    def get_realtime_daily(self, ts_codes: str | list[str]) -> list[dict[str, Any]]:
        codes: list[str]
        if isinstance(ts_codes, str):
            codes = [item.strip() for item in ts_codes.split(",") if item.strip()]
        else:
            codes = [str(item or "").strip() for item in ts_codes if str(item or "").strip()]
        normalized_codes = [self._normalize_rt_code(item) for item in codes]
        normalized_codes = [item for item in normalized_codes if item]
        if not normalized_codes:
            raise DataProviderError("缺少实时日线股票代码。", 400)
        if len(normalized_codes) > 6000:
            raise DataProviderError("实时日线单次最多支持 6000 只股票。", 400)

        pro = self._client()
        try:
            df = pro.rt_k(ts_code=",".join(normalized_codes))
        except Exception as exc:
            raise DataProviderError(f"Tushare 实时日线获取失败：{exc}", 502) from exc

        if df is None or df.empty:
            raise DataProviderError("没有获取到实时日线数据，请检查 rt_k 权限或股票代码。", 404)

        numeric_fields = {
            "pre_close",
            "high",
            "open",
            "low",
            "close",
            "vol",
            "amount",
            "num",
            "ask_price1",
            "ask_volume1",
            "bid_price1",
            "bid_volume1",
        }
        rows = []
        for row in df.fillna("").to_dict("records"):
            item: dict[str, Any] = {}
            for key, value in row.items():
                text_key = str(key)
                item[text_key] = _safe_float(value) if text_key in numeric_fields else (str(value).strip() if value is not None else "")
            item["ts_code"] = str(item.get("ts_code") or "").strip().upper()
            rows.append(item)
        return rows

    def get_top_list(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="top_list",
            label="龙虎榜数据",
            trade_date=trade_date,
            fields="trade_date,ts_code,name,close,pct_change,turnover_rate,amount,net_amount,reason",
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(
                df,
                numeric_fields=("close", "pct_change", "turnover_rate", "amount", "net_amount"),
            ),
        }

    def get_top_inst(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="top_inst",
            label="机构交易",
            trade_date=trade_date,
            fields="trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy,side,reason",
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(
                df,
                numeric_fields=("buy", "buy_rate", "sell", "sell_rate", "net_buy"),
            ),
        }

    def get_hot_money_detail(self, trade_date: str | None = None) -> dict[str, Any]:
        cache_key = trade_date or "latest"
        cached = self._hot_money_detail_cache.get(cache_key)
        if cached is not None:
            cached_at, payload = cached
            if time.time() - cached_at <= self.board_cache_ttl_seconds:
                return payload

        store_cached = self._read_hot_money_detail_store_cache(trade_date, cache_key)
        if store_cached is not None:
            return store_cached

        file_cached = self._read_hot_money_detail_file_cache(cache_key)
        if file_cached is not None:
            self._hot_money_detail_cache[cache_key] = (time.time(), file_cached)
            self._write_hot_money_detail_store_cache(file_cached)
            return file_cached

        try:
            df, actual_trade_date = self._fetch_market_dataframe(
                api_name="hm_detail",
                label="游资数据",
                trade_date=trade_date,
                candidate_days=1 if trade_date else 2,
            )
        except DataProviderError as exc:
            stale_cached = self._read_hot_money_detail_file_cache(cache_key, ignore_ttl=True)
            if stale_cached is not None and _is_tushare_rate_limit_error(exc.message):
                self._hot_money_detail_cache[cache_key] = (time.time(), stale_cached)
                self._write_hot_money_detail_store_cache(stale_cached)
                return stale_cached
            raise
        items = _standardize_market_rows(
            df,
            numeric_fields=("buy_amount", "sell_amount", "net_amount"),
        )
        for item in items:
            item["tag"] = _hot_money_tag(item.get("net_amount"))
        payload = {
            "trade_date": actual_trade_date,
            "items": items,
        }
        self._hot_money_detail_cache[cache_key] = (time.time(), payload)
        self._write_hot_money_detail_file_cache(cache_key, payload)
        self._write_hot_money_detail_store_cache(payload)
        return payload

    def get_limit_list(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="limit_list_d",
            label="涨跌停列表",
            trade_date=trade_date,
            fields="trade_date,ts_code,name,close,pct_chg,amp,fc_ratio,fl_ratio,fd_amount,first_time,last_time,open_times,strth,limit,reason,limit_times",
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(
                df,
                numeric_fields=("close", "pct_chg", "amp", "fc_ratio", "fl_ratio", "fd_amount", "open_times", "strth", "limit_times"),
            ),
        }

    def get_limit_step(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="limit_step",
            label="连板天梯",
            trade_date=trade_date,
            fields="trade_date,ts_code,name,close,pct_chg,change_tag,industry,concept,amount,turnover_rate,limit_times,up_stat,nums",
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_limit_step_rows(df),
        }

    def get_limit_concept_list(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="limit_cpt_list",
            label="涨停板块",
            trade_date=trade_date,
            fields="trade_date,ts_code,name,days,up_stat,cons_nums,up_nums,pct_chg,rank,open_num,count,limit_count,turnover_rate,cmc",
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(
                df,
                numeric_fields=("days", "cons_nums", "up_nums", "pct_chg", "rank", "open_num", "count", "limit_count", "turnover_rate", "cmc"),
            ),
        }

    def get_kpl_list(self, trade_date: str | None = None) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="kpl_list",
            label="开盘啦榜单",
            trade_date=trade_date,
            fields="ts_code,name,trade_date,theme,pct_chg,amount,turnover_rate,tag,status,net_change,bid_amount,lu_desc",
            candidate_days=5,
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(
                df,
                numeric_fields=("pct_chg", "amount", "turnover_rate", "net_change", "bid_amount"),
            ),
        }

    def get_kpl_concept_cons(
        self,
        trade_date: str | None = None,
        ts_code: str | None = None,
        con_code: str | None = None,
    ) -> dict[str, Any]:
        df, actual_trade_date = self._fetch_market_dataframe(
            api_name="kpl_concept_cons",
            label="开盘啦题材成分",
            trade_date=trade_date,
            fields="ts_code,name,con_name,con_code,trade_date,desc,hot_num",
            extra_params={
                "ts_code": str(ts_code or "").strip() or None,
                "con_code": str(con_code or "").strip().upper() or None,
            },
            candidate_days=5,
        )
        return {
            "trade_date": actual_trade_date,
            "items": _standardize_market_rows(df, numeric_fields=("hot_num",)),
        }

    def get_hot_money_list(self, name: str | None = None, force_refresh: bool = False) -> list[dict[str, Any]]:
        cleaned_name = (name or "").strip()
        if not cleaned_name and not force_refresh and self._hot_money_cache is not None:
            cached_at, cached_items = self._hot_money_cache
            if time.time() - cached_at <= self.cache_ttl_seconds:
                return cached_items

        pro = self._client()
        try:
            df = pro.hm_list(name=cleaned_name or None, fields="name,desc,orgs")
        except Exception as exc:
            raise DataProviderError(f"Tushare 游资名录获取失败：{exc}", 502) from exc

        items = _standardize_market_rows(df if df is not None else pd.DataFrame(), numeric_fields=())
        if not cleaned_name:
            self._hot_money_cache = (time.time(), items)
        return items

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

    @staticmethod
    def _board_kwargs(row: Any, source: str) -> dict[str, str]:
        config = _board_source_config(source)
        getter = row.get if hasattr(row, "get") else row.__getitem__
        return {
            "ts_code": str(getter("ts_code", "")),
            "name": str(getter("name", "")),
            "source": source,
            "source_label": str(config["label"]),
            "idx_type": str(getter("idx_type", "")),
            "type_key": _reverse_board_type(source, str(getter("idx_type", ""))),
            "trade_date": str(getter("trade_date", "")),
            "leading": str(getter("leading", "")),
            "leading_code": str(getter("leading_code", "")),
            "pct_change": str(getter("pct_change", "")),
            "leading_pct": str(getter("leading_pct", "")),
            "total_mv": str(getter("total_mv", "")),
            "turnover_rate": str(getter("turnover_rate", "")),
            "up_num": str(getter("up_num", "")),
            "down_num": str(getter("down_num", "")),
            "level": str(getter("level", "")),
        }

    def _read_board_cache(self, cache_key: str) -> pd.DataFrame | None:
        cached = self._board_cache.get(cache_key)
        if not cached:
            return None
        timestamp, df = cached
        if time.time() - timestamp > self.board_cache_ttl_seconds:
            self._board_cache.pop(cache_key, None)
            return None
        return df

    def _read_board_member_cache(self, cache_key: str) -> list[dict[str, str]] | None:
        cached = self._board_member_cache.get(cache_key)
        if not cached:
            return None
        timestamp, rows = cached
        if time.time() - timestamp > self.board_cache_ttl_seconds:
            self._board_member_cache.pop(cache_key, None)
            return None
        return rows

    def _hot_money_detail_cache_file(self, cache_key: str) -> Path:
        safe_key = "".join(ch for ch in cache_key if ch.isalnum() or ch in {"_", "-"})
        if not safe_key:
            safe_key = "latest"
        return self._hot_money_detail_cache_dir / f"{safe_key}.json"

    def _read_hot_money_detail_file_cache(
        self,
        cache_key: str,
        ignore_ttl: bool = False,
    ) -> dict[str, Any] | None:
        cache_file = self._hot_money_detail_cache_file(cache_key)
        if not cache_file.exists():
            return None
        if not ignore_ttl and time.time() - cache_file.stat().st_mtime > self.board_cache_ttl_seconds:
            return None
        try:
            import json

            payload = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        items = payload.get("items", [])
        if not isinstance(items, list):
            return None
        return payload

    def _write_hot_money_detail_file_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        cache_file = self._hot_money_detail_cache_file(cache_key)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            import json

            cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            return

    def _read_hot_money_detail_store_cache(
        self,
        trade_date: str | None,
        cache_key: str,
    ) -> dict[str, Any] | None:
        if not self._hot_money_store.enabled:
            return None
        try:
            payload = self._hot_money_store.get_payload(trade_date)
        except HotMoneyStoreError as exc:
            logger.warning("读取 MySQL 游资缓存失败：%s", exc)
            return None
        if payload is None:
            return None
        self._hot_money_detail_cache[cache_key] = (time.time(), payload)
        trade_day = str(payload.get("trade_date", "") or "").strip()
        if trade_day:
            self._hot_money_detail_cache[trade_day] = (time.time(), payload)
        return payload

    def _write_hot_money_detail_store_cache(self, payload: dict[str, Any]) -> None:
        if not self._hot_money_store.enabled:
            return
        try:
            self._hot_money_store.save_payload(payload)
        except HotMoneyStoreError as exc:
            logger.warning("写入 MySQL 游资缓存失败：%s", exc)

    def _read_stock_basic_store_cache(self, ts_code: str, trade_date: str | None = None) -> dict[str, Any]:
        if not self._stock_basic_store.enabled:
            return {}
        try:
            payload = self._stock_basic_store.get_payload(ts_code=ts_code, trade_date=trade_date)
        except StockBasicStoreError as exc:
            logger.warning("读取 MySQL 股票基础资料缓存失败：%s", exc)
            return {}
        if not isinstance(payload, dict):
            return {}
        bak_basic = payload.get("bak_basic")
        return dict(bak_basic) if isinstance(bak_basic, dict) else {}

    def _write_stock_basic_store_cache(self, stock: dict[str, Any], bak_basic: dict[str, Any]) -> None:
        if not self._stock_basic_store.enabled:
            return
        try:
            self._stock_basic_store.save_payload(stock=stock, bak_basic=bak_basic)
        except StockBasicStoreError as exc:
            logger.warning("写入 MySQL 股票基础资料缓存失败：%s", exc)

    def _normalize_rt_code(self, value: str) -> str:
        cleaned = str(value or "").strip().upper()
        if not cleaned:
            return ""
        if "." in cleaned:
            return cleaned
        return self.resolve_stock(cleaned).ts_code

    def _fetch_board_snapshot(self, source: str, idx_type: str) -> pd.DataFrame:
        config = _board_source_config(source)
        pro = self._client()
        api_name = config["index_api"]
        fields = config["index_fields"]
        last_error: Exception | None = None
        for day in _recent_trade_dates(12):
            try:
                df = getattr(pro, api_name)(trade_date=day, idx_type=idx_type, fields=fields)
            except Exception as exc:
                last_error = exc
                continue
            if df is not None and not df.empty:
                return df.fillna("")
        try:
            df = getattr(pro, api_name)(idx_type=idx_type, fields=fields)
        except Exception as exc:
            last_error = exc
            df = None
        if df is not None and not df.empty:
            return df.fillna("")
        if last_error:
            raise DataProviderError(_friendly_tushare_board_error(config["label"], "列表获取失败", last_error), 502) from last_error
        return pd.DataFrame()

    def _fetch_market_dataframe(
        self,
        api_name: str,
        label: str,
        trade_date: str | None = None,
        fields: str = "",
        extra_params: dict[str, Any] | None = None,
        candidate_days: int = 12,
    ) -> tuple[pd.DataFrame, str]:
        pro = self._client()
        params = dict(extra_params or {})
        last_error: Exception | None = None
        for day in _trade_date_candidates(trade_date, candidate_days):
            try:
                call_params = {"trade_date": day, **params}
                if fields:
                    call_params["fields"] = fields
                df = getattr(pro, api_name)(**call_params)
            except Exception as exc:
                last_error = exc
                continue
            if df is not None and not df.empty:
                return df.fillna(""), day
        if last_error:
            raise DataProviderError(_friendly_tushare_market_error(label, last_error), 502) from last_error
        return pd.DataFrame(), trade_date or ""

    @staticmethod
    def _standardize_board_members(df: pd.DataFrame, source: str) -> list[dict[str, str]]:
        rows = []
        for _, row in df.fillna("").iterrows():
            con_code = str(row.get("con_code", ""))
            rows.append(
                {
                    "source": source,
                    "trade_date": str(row.get("trade_date", "")),
                    "ts_code": str(row.get("ts_code", "")),
                    "con_code": con_code,
                    "symbol": con_code.split(".")[0] if "." in con_code else con_code,
                    "name": str(row.get("name", "") or row.get("con_name", "")),
                }
            )
        return rows


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


def _json_safe_scalar(value: Any) -> Any:
    if pd.isna(value):
        return ""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return round(value, 4)
    return str(value).strip()


def _friendly_tushare_board_error(label: str, action: str, exc: Exception) -> str:
    text = str(exc)
    if "Failed to resolve" in text or "NameResolutionError" in text:
        return f"Tushare {label}{action}：当前环境无法访问 api.waditu.com（DNS 解析失败），请在可联网环境或 Render 上重试。"
    return f"Tushare {label}{action}：{text}"


def _friendly_tushare_market_error(label: str, exc: Exception) -> str:
    text = str(exc)
    if "Failed to resolve" in text or "NameResolutionError" in text:
        return f"Tushare {label}获取失败：当前环境无法访问 api.waditu.com（DNS 解析失败），请在可联网环境或 Render 上重试。"
    return f"Tushare {label}获取失败：{text}"


def _is_tushare_rate_limit_error(message: str) -> bool:
    text = str(message or "")
    return "频率超限" in text or "limit" in text.lower()


def _minute_datetime(value: str, is_end: bool) -> str:
    day = f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return f"{day} {'23:59:59' if is_end else '00:00:00'}"


def _supported_levels_text() -> str:
    return "、".join(LEVELS)


_BOARD_SOURCE_CONFIG = {
    "dc": {
        "label": "东方财富板块",
        "index_api": "dc_index",
        "member_api": "dc_member",
        "index_fields": "ts_code,trade_date,name,leading,leading_code,pct_change,leading_pct,total_mv,turnover_rate,up_num,down_num,idx_type,level",
        "member_fields": "trade_date,ts_code,con_code,name",
        "types": {
            "industry": "行业板块",
            "concept": "概念板块",
            "region": "地域板块",
        },
    },
    "tdx": {
        "label": "通达信板块",
        "index_api": "tdx_index",
        "member_api": "tdx_member",
        "index_fields": "ts_code,trade_date,name,idx_type,level",
        "member_fields": "trade_date,ts_code,con_code,name",
        "types": {
            "industry": "行业板块",
            "concept": "概念板块",
            "style": "风格板块",
            "region": "地域板块",
        },
    },
    "ths": {
        "label": "同花顺板块",
        "index_api": "ths_index",
        "member_api": "ths_member",
        "index_fields": "ts_code,trade_date,name,count,exchange,list_date,type",
        "member_fields": "trade_date,ts_code,con_code,con_name",
        "types": {
            "concept": "N",
            "industry": "I",
            "region": "R",
            "feature": "S",
            "style": "ST",
            "theme": "TH",
            "broad": "BB",
        },
    },
}


def _board_source_config(source: str) -> dict[str, Any]:
    cleaned = (source or "").strip().lower()
    if cleaned not in _BOARD_SOURCE_CONFIG:
        raise DataProviderError("板块来源只支持东方财富、通达信、同花顺。", 400)
    return _BOARD_SOURCE_CONFIG[cleaned]


def _normalize_board_type(source: str, value: str) -> str:
    config = _board_source_config(source)
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"all", "全部", "全部板块"}:
        return ""
    if cleaned in config["types"]:
        return config["types"][cleaned]
    if cleaned in config["types"].values():
        return cleaned
    supported = "、".join(config["types"].keys())
    raise DataProviderError(f"{config['label']}类型只支持 {supported}。", 400)


def _reverse_board_type(source: str, idx_type: str) -> str:
    config = _board_source_config(source)
    for key, value in config["types"].items():
        if value == idx_type:
            return key
    return ""


def _recent_trade_dates(days: int, preferred: str | None = None) -> list[str]:
    if preferred:
        return [preferred]
    today = date.today()
    return [(today - timedelta(days=offset)).strftime("%Y%m%d") for offset in range(days)]


def _trade_date_candidates(preferred: str | None, days: int) -> list[str]:
    dates: list[str] = []
    if preferred:
        dates.append(preferred)
    today = date.today()
    for offset in range(days):
        day = (today - timedelta(days=offset)).strftime("%Y%m%d")
        if day not in dates:
            dates.append(day)
    return dates


def _standardize_market_rows(df: pd.DataFrame, numeric_fields: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if df is None or df.empty:
        return rows

    for _, row in df.fillna("").iterrows():
        item: dict[str, Any] = {}
        for column in df.columns:
            value = row.get(column, "")
            if column in numeric_fields:
                item[column] = _safe_float(value)
            else:
                item[column] = str(value).strip()
        rows.append(item)
    return rows


def _standardize_limit_step_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = _standardize_market_rows(
        df,
        numeric_fields=("close", "pct_chg", "amount", "turnover_rate", "limit_times", "nums"),
    )
    for item in rows:
        continue_num = _coerce_board_count(
            item.get("nums"),
            item.get("continue_num"),
            item.get("up_stat"),
        )
        item["continue_num"] = continue_num
        item["nums"] = continue_num
        raw_limit_times = _coerce_board_count(item.get("limit_times"))
        item["limit_times"] = raw_limit_times or continue_num
    return rows


def _hot_money_tag(value: Any) -> str:
    amount = _safe_float(value)
    if amount is None:
        return "平衡"
    if amount > 0:
        return "净买入"
    if amount < 0:
        return "净卖出"
    return "平衡"


def _coerce_board_count(*values: Any) -> int:
    for value in values:
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return int(numeric)
        if isinstance(value, str):
            match = re.search(r"(\d+)", value)
            if match:
                return int(match.group(1))
    return 0


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _env_value(name: str) -> str | None:
    return _shared_raw_env_value(name)


def _safe_env_int(name: str, default: int) -> int:
    return _shared_safe_env_int(name, default)


def _mysql_dsn_from_env() -> str:
    return _shared_mysql_dsn_from_env()
