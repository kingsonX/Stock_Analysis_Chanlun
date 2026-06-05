from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


class WatchlistStoreError(RuntimeError):
    pass


class AnalysisWatchlistStore:
    def __init__(
        self,
        dsn: str | None = None,
        min_size: int = 1,
        max_size: int = 4,
        connection_timeout_seconds: float = 2.0,
        failure_cooldown_seconds: float = 90.0,
    ):
        self.dsn = (dsn or "").strip()
        self.min_size = max(1, int(min_size))
        self.max_size = max(self.min_size, int(max_size))
        self.connection_timeout_seconds = max(0.2, float(connection_timeout_seconds))
        self.failure_cooldown_seconds = max(1.0, float(failure_cooldown_seconds))
        self._pool = None
        self._schema_ready = False
        self._disabled_until = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    def list_entries(self, query: str = "") -> list[dict[str, Any]]:
        if not self.enabled:
            return []

        cleaned_query = str(query or "").strip()
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                if cleaned_query:
                    like = f"%{cleaned_query}%"
                    cur.execute(
                        """
                        select ts_code, symbol, name, area, industry, market, exchange, list_date,
                               bak_trade_date, raw_payload, created_at, updated_at
                        from app_private.analysis_watchlist_entries
                        where ts_code ilike %s
                           or symbol ilike %s
                           or name ilike %s
                           or area ilike %s
                           or industry ilike %s
                        order by updated_at desc, ts_code asc
                        """,
                        (like, like, like, like, like),
                    )
                else:
                    cur.execute(
                        """
                        select ts_code, symbol, name, area, industry, market, exchange, list_date,
                               bak_trade_date, raw_payload, created_at, updated_at
                        from app_private.analysis_watchlist_entries
                        order by updated_at desc, ts_code asc
                        """
                    )
                return [_serialize_entry_row(row) for row in cur.fetchall()]
        except WatchlistStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise WatchlistStoreError(f"读取智能盯盘数据库失败：{exc}") from exc

    def get_entry(self, ts_code: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            return None

        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    select ts_code, symbol, name, area, industry, market, exchange, list_date,
                           bak_trade_date, raw_payload, created_at, updated_at
                    from app_private.analysis_watchlist_entries
                    where ts_code = %s
                    """,
                    (cleaned_code,),
                )
                row = cur.fetchone()
                return _serialize_entry_row(row) if row else None
        except WatchlistStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise WatchlistStoreError(f"读取智能盯盘单股缓存失败：{exc}") from exc

    def save_entry(self, stock: dict[str, Any], bak_basic: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return

        stock_payload = dict(stock or {})
        bak_payload = dict(bak_basic or stock_payload.get("bak_basic") or {})
        ts_code = str(stock_payload.get("ts_code") or bak_payload.get("ts_code") or "").strip().upper()
        if not ts_code:
            return

        stock_payload["ts_code"] = ts_code
        payload = {"stock": stock_payload, "bak_basic": bak_payload}
        row = (
            ts_code,
            str(stock_payload.get("symbol") or "").strip(),
            str(stock_payload.get("name") or bak_payload.get("name") or "").strip(),
            str(stock_payload.get("area") or bak_payload.get("area") or "").strip(),
            str(stock_payload.get("industry") or bak_payload.get("industry") or "").strip(),
            str(stock_payload.get("market") or "").strip(),
            str(stock_payload.get("exchange") or "").strip(),
            str(stock_payload.get("list_date") or bak_payload.get("list_date") or "").strip(),
            _normalize_trade_date_text(bak_payload.get("trade_date")),
            json.dumps(payload, ensure_ascii=False),
        )

        try:
            with self._connection() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        self._ensure_schema(cur)
                        cur.execute(
                            """
                            insert into app_private.analysis_watchlist_entries (
                              ts_code, symbol, name, area, industry, market, exchange, list_date,
                              bak_trade_date, raw_payload, created_at, updated_at
                            )
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, timezone('utc', now()), timezone('utc', now()))
                            on conflict (ts_code) do update set
                              symbol = excluded.symbol,
                              name = excluded.name,
                              area = excluded.area,
                              industry = excluded.industry,
                              market = excluded.market,
                              exchange = excluded.exchange,
                              list_date = excluded.list_date,
                              bak_trade_date = excluded.bak_trade_date,
                              raw_payload = excluded.raw_payload,
                              updated_at = excluded.updated_at
                            """,
                            row,
                        )
        except WatchlistStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise WatchlistStoreError(f"写入智能盯盘数据库失败：{exc}") from exc

    def delete_entry(self, ts_code: str) -> bool:
        if not self.enabled:
            return False
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            return False

        try:
            with self._connection() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        self._ensure_schema(cur)
                        cur.execute("delete from app_private.analysis_watchlist_entries where ts_code = %s", (cleaned_code,))
                        return cur.rowcount > 0
        except WatchlistStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise WatchlistStoreError(f"删除智能盯盘数据库记录失败：{exc}") from exc

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            self._schema_ready = False

    def _connection(self):
        if self._disabled_until > time.time():
            raise WatchlistStoreError("智能盯盘数据库连接暂时熔断，等待冷却后再试。")
        pool = self._get_pool()
        return pool.connection(timeout=self.connection_timeout_seconds)

    def _get_pool(self):
        if self._pool is not None:
            return self._pool
        if not self.enabled:
            raise WatchlistStoreError("未配置 SUPABASE_DB_URL，无法使用智能盯盘数据库。")
        try:
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool
        except Exception as exc:
            raise WatchlistStoreError("未安装 psycopg / psycopg_pool，无法启用 PostgreSQL session pool。") from exc

        try:
            self._pool = ConnectionPool(
                conninfo=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                open=True,
                kwargs={"autocommit": False, "row_factory": dict_row},
            )
            return self._pool
        except Exception as exc:
            raise WatchlistStoreError(f"智能盯盘 PostgreSQL session pool 初始化失败：{exc}") from exc

    def _trip_circuit(self) -> None:
        self.close()
        self._disabled_until = time.time() + self.failure_cooldown_seconds

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute("create schema if not exists app_private")
        cur.execute(
            """
            create table if not exists app_private.analysis_watchlist_entries (
              ts_code text primary key,
              symbol text not null default '',
              name text not null default '',
              area text not null default '',
              industry text not null default '',
              market text not null default '',
              exchange text not null default '',
              list_date text not null default '',
              bak_trade_date date null,
              raw_payload jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default timezone('utc', now()),
              updated_at timestamptz not null default timezone('utc', now())
            )
            """
        )
        cur.execute("select count(*) as total from app_private.analysis_watchlist_entries")
        summary = cur.fetchone() or {}
        if int(summary.get("total") or 0) == 0:
            cur.execute("select to_regclass('app_private.stock_basic_snapshots') as table_name")
            existing = cur.fetchone() or {}
            if existing.get("table_name"):
                cur.execute(
                    """
                    insert into app_private.analysis_watchlist_entries (
                      ts_code, symbol, name, area, industry, market, exchange, list_date,
                      bak_trade_date, raw_payload, created_at, updated_at
                    )
                    select ts_code, symbol, name, area, industry, market, exchange, list_date,
                           trade_date, raw_payload, timezone('utc', now()), timezone('utc', now())
                    from app_private.stock_basic_snapshots
                    on conflict (ts_code) do nothing
                    """
                )
        self._schema_ready = True


def _normalize_trade_date_text(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("-", "").replace("/", "")
    if len(text) != 8 or not text.isdigit():
        return None
    return datetime.strptime(text, "%Y%m%d").date()


def _coerce_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            logger.warning("智能盯盘 raw_payload 解析失败，返回空对象。")
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _serialize_entry_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = _coerce_payload(row.get("raw_payload"))
    stock = dict(payload.get("stock") or {})
    bak_basic = dict(payload.get("bak_basic") or {})
    stock.setdefault("ts_code", str(row.get("ts_code") or "").strip().upper())
    stock.setdefault("symbol", str(row.get("symbol") or "").strip())
    stock.setdefault("name", str(row.get("name") or "").strip())
    stock.setdefault("area", str(row.get("area") or "").strip())
    stock.setdefault("industry", str(row.get("industry") or "").strip())
    stock.setdefault("market", str(row.get("market") or "").strip())
    stock.setdefault("exchange", str(row.get("exchange") or "").strip())
    stock.setdefault("list_date", str(row.get("list_date") or "").strip())
    return {
        "ts_code": stock.get("ts_code", ""),
        "symbol": stock.get("symbol", ""),
        "name": stock.get("name", ""),
        "area": stock.get("area", ""),
        "industry": stock.get("industry", ""),
        "market": stock.get("market", ""),
        "exchange": stock.get("exchange", ""),
        "list_date": stock.get("list_date", ""),
        "stock": stock,
        "bak_basic": bak_basic,
        "created_at": _format_timestamp(row.get("created_at")),
        "updated_at": _format_timestamp(row.get("updated_at")),
    }


def _format_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "").strip()
