from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timedelta
from typing import Any

from .mysql_store import MySQLStoreConnectionError, mysql_connection

logger = logging.getLogger(__name__)


class HotMoneyStoreError(RuntimeError):
    pass


class HotMoneyDailyTradeStore:
    def __init__(
        self,
        dsn: str | None = None,
        min_size: int = 1,
        max_size: int = 4,
        latest_window_days: int = 10,
        connection_timeout_seconds: float = 2.0,
        failure_cooldown_seconds: float = 90.0,
    ):
        self.dsn = (dsn or "").strip()
        self.min_size = max(1, int(min_size))
        self.max_size = max(self.min_size, int(max_size))
        self.latest_window_days = max(1, int(latest_window_days))
        self.connection_timeout_seconds = max(0.2, float(connection_timeout_seconds))
        self.failure_cooldown_seconds = max(1.0, float(failure_cooldown_seconds))
        self._schema_ready = False
        self._disabled_until = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    def get_payload(self, trade_date: str | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        target_date = _normalize_trade_date_text(trade_date)
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                if target_date:
                    cur.execute(
                        """
                        select trade_date, status, record_count
                        from hot_money_daily_fetches
                        where trade_date = %s
                        """,
                        (target_date,),
                    )
                else:
                    cutoff = date.today() - timedelta(days=self.latest_window_days)
                    cur.execute(
                        """
                        select trade_date, status, record_count
                        from hot_money_daily_fetches
                        where trade_date >= %s
                        order by trade_date desc
                        limit 1
                        """,
                        (cutoff,),
                    )
                summary = cur.fetchone()
                if not summary:
                    return None

                cur.execute(
                    """
                    select raw_payload
                    from hot_money_daily_trades
                    where trade_date = %s
                    order by abs(ifnull(net_amount, 0)) desc, ifnull(buy_amount, 0) desc, id asc
                    """,
                    (summary["trade_date"],),
                )
                items = [_coerce_payload(row.get("raw_payload")) for row in cur.fetchall()]
                return {
                    "trade_date": summary["trade_date"].strftime("%Y%m%d"),
                    "items": items,
                    "status": summary.get("status", "success"),
                    "record_count": int(summary.get("record_count") or len(items)),
                }
        except HotMoneyStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise HotMoneyStoreError(f"读取 MySQL 游资缓存失败：{exc}") from exc

    def save_payload(self, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return

        trade_date = _normalize_trade_date_text(payload.get("trade_date"))
        if not trade_date:
            return

        items = list(payload.get("items") or [])
        rows = [_serialize_item(trade_date, item) for item in items]

        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    insert into hot_money_daily_fetches (
                      trade_date, source_api, status, record_count, fetched_at
                    )
                    values (%s, 'hm_detail', %s, %s, current_timestamp)
                    on duplicate key update
                      source_api = values(source_api),
                      status = values(status),
                      record_count = values(record_count),
                      fetched_at = values(fetched_at),
                      updated_at = current_timestamp
                    """,
                    (trade_date, "success" if rows else "empty", len(rows)),
                )
                cur.execute("delete from hot_money_daily_trades where trade_date = %s", (trade_date,))
                if rows:
                    cur.executemany(
                        """
                        insert into hot_money_daily_trades (
                          trade_date, ts_code, ts_name, buy_amount, sell_amount, net_amount,
                          hm_name, hm_orgs, tag, raw_payload, fetched_at
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, current_timestamp)
                        """,
                        rows,
                    )
        except HotMoneyStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise HotMoneyStoreError(f"写入 MySQL 游资缓存失败：{exc}") from exc

    def close(self) -> None:
        self._schema_ready = False

    def _connection(self):
        if self._disabled_until > time.time():
            raise HotMoneyStoreError("MySQL 游资缓存连接暂时熔断，等待冷却后再试。")
        try:
            return mysql_connection(self.dsn, connect_timeout_seconds=self.connection_timeout_seconds)
        except MySQLStoreConnectionError as exc:
            raise HotMoneyStoreError(str(exc)) from exc

    def _trip_circuit(self) -> None:
        self.close()
        self._disabled_until = time.time() + self.failure_cooldown_seconds

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute(
            """
            create table if not exists hot_money_daily_fetches (
              trade_date date not null primary key,
              source_api varchar(32) not null default 'hm_detail',
              status varchar(16) not null default 'success',
              record_count int not null default 0,
              fetched_at datetime not null default current_timestamp,
              updated_at datetime not null default current_timestamp on update current_timestamp
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        cur.execute(
            """
            create table if not exists hot_money_daily_trades (
              id bigint unsigned not null auto_increment primary key,
              trade_date date not null,
              ts_code varchar(16) not null default '',
              ts_name varchar(64) not null default '',
              buy_amount decimal(20, 4) not null default 0,
              sell_amount decimal(20, 4) not null default 0,
              net_amount decimal(20, 4) not null default 0,
              hm_name varchar(128) not null default '',
              hm_orgs varchar(255) not null default '',
              tag varchar(64) not null default '',
              raw_payload json not null,
              fetched_at datetime not null default current_timestamp,
              key idx_hot_money_trade_date (trade_date),
              key idx_hot_money_ts_code (ts_code),
              key idx_hot_money_hm_name (hm_name)
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


def _serialize_item(trade_date: date, item: dict[str, Any]) -> tuple[Any, ...]:
    raw_payload = json.dumps(item, ensure_ascii=False)
    return (
        trade_date,
        _as_text(item.get("ts_code")),
        _as_text(item.get("ts_name") or item.get("name")),
        _as_float(item.get("buy_amount")),
        _as_float(item.get("sell_amount")),
        _as_float(item.get("net_amount")),
        _as_text(item.get("hm_name")),
        _as_text(item.get("hm_orgs")),
        _as_text(item.get("tag")),
        raw_payload,
    )


def _coerce_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            logger.warning("游资缓存 raw_payload 解析失败，返回空对象。")
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
