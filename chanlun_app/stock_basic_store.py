from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


class StockBasicStoreError(RuntimeError):
    pass


class StockBasicCacheStore:
    def __init__(
        self,
        dsn: str | None = None,
        min_size: int = 1,
        max_size: int = 4,
    ):
        self.dsn = (dsn or "").strip()
        self.min_size = max(1, int(min_size))
        self.max_size = max(self.min_size, int(max_size))
        self._pool = None
        self._schema_ready = False

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    def get_payload(self, ts_code: str, trade_date: str | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            return None

        target_day = _normalize_trade_date_text(trade_date)
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select trade_date, raw_payload
                from app_private.stock_basic_snapshots
                where ts_code = %s
                """,
                (cleaned_code,),
            )
            row = cur.fetchone()
            if not row:
                return None

            payload = _coerce_payload(row.get("raw_payload"))
            if target_day:
                payload_day = _normalize_trade_date_text((payload.get("bak_basic") or {}).get("trade_date"))
                if payload_day and payload_day != target_day:
                    return None
            return payload

    def save_payload(self, stock: dict[str, Any], bak_basic: dict[str, Any]) -> None:
        if not self.enabled:
            return

        stock_payload = dict(stock or {})
        bak_payload = dict(bak_basic or {})
        ts_code = str(stock_payload.get("ts_code") or bak_payload.get("ts_code") or "").strip().upper()
        if not ts_code:
            return

        stock_payload["ts_code"] = ts_code
        payload = {"stock": stock_payload, "bak_basic": bak_payload}
        trade_day = _normalize_trade_date_text(bak_payload.get("trade_date"))
        row = (
            ts_code,
            str(stock_payload.get("symbol") or "").strip(),
            str(stock_payload.get("name") or bak_payload.get("name") or "").strip(),
            str(stock_payload.get("area") or bak_payload.get("area") or "").strip(),
            str(stock_payload.get("industry") or bak_payload.get("industry") or "").strip(),
            str(stock_payload.get("market") or "").strip(),
            str(stock_payload.get("exchange") or "").strip(),
            str(stock_payload.get("list_date") or bak_payload.get("list_date") or "").strip(),
            trade_day,
            json.dumps(payload, ensure_ascii=False),
        )

        with self._connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    self._ensure_schema(cur)
                    cur.execute(
                        """
                        insert into app_private.stock_basic_snapshots (
                          ts_code, symbol, name, area, industry, market, exchange, list_date,
                          trade_date, raw_payload, updated_at
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, timezone('utc', now()))
                        on conflict (ts_code) do update set
                          symbol = excluded.symbol,
                          name = excluded.name,
                          area = excluded.area,
                          industry = excluded.industry,
                          market = excluded.market,
                          exchange = excluded.exchange,
                          list_date = excluded.list_date,
                          trade_date = excluded.trade_date,
                          raw_payload = excluded.raw_payload,
                          updated_at = excluded.updated_at
                        """,
                        row,
                    )

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            self._schema_ready = False

    def _connection(self):
        pool = self._get_pool()
        return pool.connection()

    def _get_pool(self):
        if self._pool is not None:
            return self._pool
        if not self.enabled:
            raise StockBasicStoreError("未配置 SUPABASE_DB_URL，无法使用股票基础资料数据库缓存。")
        try:
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool
        except Exception as exc:
            raise StockBasicStoreError("未安装 psycopg / psycopg_pool，无法启用 PostgreSQL session pool。") from exc

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
            raise StockBasicStoreError(f"股票基础资料 PostgreSQL session pool 初始化失败：{exc}") from exc

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute("select to_regclass('app_private.stock_basic_snapshots') as table_name")
        existing = cur.fetchone()
        if existing and existing.get("table_name"):
            self._schema_ready = True
            return
        cur.execute("create schema if not exists app_private")
        cur.execute(
            """
            create table if not exists app_private.stock_basic_snapshots (
              ts_code text primary key,
              symbol text not null default '',
              name text not null default '',
              area text not null default '',
              industry text not null default '',
              market text not null default '',
              exchange text not null default '',
              list_date text not null default '',
              trade_date date null,
              raw_payload jsonb not null default '{}'::jsonb,
              updated_at timestamptz not null default timezone('utc', now())
            )
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
            logger.warning("股票基础资料缓存 raw_payload 解析失败，返回空对象。")
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}
