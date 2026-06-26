from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from typing import Any

from .mysql_store import MySQLStoreConnectionError, mysql_connection

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
                    like = f"%{cleaned_query.lower()}%"
                    cur.execute(
                        """
                        select ts_code, symbol, name, area, industry, market, exchange, list_date,
                               bak_trade_date, raw_payload, created_at, updated_at
                        from analysis_watchlist_entries
                        where lower(ts_code) like %s
                           or lower(symbol) like %s
                           or lower(name) like %s
                           or lower(area) like %s
                           or lower(industry) like %s
                        order by updated_at desc, ts_code asc
                        """,
                        (like, like, like, like, like),
                    )
                else:
                    cur.execute(
                        """
                        select ts_code, symbol, name, area, industry, market, exchange, list_date,
                               bak_trade_date, raw_payload, created_at, updated_at
                        from analysis_watchlist_entries
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
                    from analysis_watchlist_entries
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
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    insert into analysis_watchlist_entries (
                      ts_code, symbol, name, area, industry, market, exchange, list_date,
                      bak_trade_date, raw_payload
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on duplicate key update
                      symbol = values(symbol),
                      name = values(name),
                      area = values(area),
                      industry = values(industry),
                      market = values(market),
                      exchange = values(exchange),
                      list_date = values(list_date),
                      bak_trade_date = values(bak_trade_date),
                      raw_payload = values(raw_payload),
                      updated_at = current_timestamp
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
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute("delete from analysis_watchlist_entries where ts_code = %s", (cleaned_code,))
                return cur.rowcount > 0
        except WatchlistStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise WatchlistStoreError(f"删除智能盯盘数据库记录失败：{exc}") from exc

    def close(self) -> None:
        self._schema_ready = False

    def _connection(self):
        if self._disabled_until > time.time():
            raise WatchlistStoreError("智能盯盘数据库连接暂时熔断，等待冷却后再试。")
        try:
            return mysql_connection(self.dsn, connect_timeout_seconds=self.connection_timeout_seconds)
        except MySQLStoreConnectionError as exc:
            raise WatchlistStoreError(str(exc)) from exc

    def _trip_circuit(self) -> None:
        self.close()
        self._disabled_until = time.time() + self.failure_cooldown_seconds

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute(
            """
            create table if not exists analysis_watchlist_entries (
              ts_code varchar(16) not null primary key,
              symbol varchar(16) not null default '',
              name varchar(64) not null default '',
              area varchar(32) not null default '',
              industry varchar(64) not null default '',
              market varchar(32) not null default '',
              exchange varchar(16) not null default '',
              list_date varchar(16) not null default '',
              bak_trade_date date null,
              raw_payload json not null,
              created_at datetime not null default current_timestamp,
              updated_at datetime not null default current_timestamp on update current_timestamp,
              key idx_watchlist_updated_at (updated_at),
              key idx_watchlist_name (name),
              key idx_watchlist_symbol (symbol)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        cur.execute("select count(*) as total from analysis_watchlist_entries")
        summary = cur.fetchone() or {}
        if int(summary.get("total") or 0) == 0:
            cur.execute("show tables like 'stock_basic_snapshots'")
            existing = cur.fetchone() or {}
            if existing:
                cur.execute(
                    """
                    insert ignore into analysis_watchlist_entries (
                      ts_code, symbol, name, area, industry, market, exchange, list_date,
                      bak_trade_date, raw_payload
                    )
                    select ts_code, symbol, name, area, industry, market, exchange, list_date,
                           trade_date, raw_payload
                    from stock_basic_snapshots
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
