from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from typing import Any

from .mysql_store import MySQLStoreConnectionError, mysql_connection

logger = logging.getLogger(__name__)


class StockBasicStoreError(RuntimeError):
    pass


class StockBasicCacheStore:
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

    def get_payload(self, ts_code: str, trade_date: str | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            return None

        target_day = _normalize_trade_date_text(trade_date)
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    select trade_date, raw_payload
                    from stock_basic_snapshots
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
        except StockBasicStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise StockBasicStoreError(f"读取股票基础资料缓存失败：{exc}") from exc

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

        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    insert into stock_basic_snapshots (
                      ts_code, symbol, name, area, industry, market, exchange, list_date,
                      trade_date, raw_payload
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
                      trade_date = values(trade_date),
                      raw_payload = values(raw_payload),
                      updated_at = current_timestamp
                    """,
                    row,
                )
        except StockBasicStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise StockBasicStoreError(f"写入股票基础资料缓存失败：{exc}") from exc

    def close(self) -> None:
        self._schema_ready = False

    def _connection(self):
        if self._disabled_until > time.time():
            raise StockBasicStoreError("股票基础资料缓存连接暂时熔断，等待冷却后再试。")
        try:
            return mysql_connection(self.dsn, connect_timeout_seconds=self.connection_timeout_seconds)
        except MySQLStoreConnectionError as exc:
            raise StockBasicStoreError(str(exc)) from exc

    def _trip_circuit(self) -> None:
        self.close()
        self._disabled_until = time.time() + self.failure_cooldown_seconds

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute(
            """
            create table if not exists stock_basic_snapshots (
              ts_code varchar(16) not null primary key,
              symbol varchar(16) not null default '',
              name varchar(64) not null default '',
              area varchar(32) not null default '',
              industry varchar(64) not null default '',
              market varchar(32) not null default '',
              exchange varchar(16) not null default '',
              list_date varchar(16) not null default '',
              trade_date date null,
              raw_payload json not null,
              updated_at datetime not null default current_timestamp on update current_timestamp,
              key idx_stock_basic_trade_date (trade_date),
              key idx_stock_basic_name (name),
              key idx_stock_basic_symbol (symbol)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
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
