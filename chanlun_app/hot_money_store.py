from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from typing import Any

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
        self._pool = None
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
                if target_date:
                    cur.execute(
                        """
                        select trade_date, status, record_count
                        from app_private.hot_money_daily_fetches
                        where trade_date = %s
                        """,
                        (target_date,),
                    )
                else:
                    cur.execute(
                        """
                        select trade_date, status, record_count
                        from app_private.hot_money_daily_fetches
                        where trade_date >= current_date - %s::int
                        order by trade_date desc
                        limit 1
                        """,
                        (self.latest_window_days,),
                    )
                summary = cur.fetchone()
                if not summary:
                    return None

                cur.execute(
                    """
                    select raw_payload
                    from app_private.hot_money_daily_trades
                    where trade_date = %s
                    order by abs(coalesce(net_amount, 0)) desc, coalesce(buy_amount, 0) desc, id asc
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
            raise HotMoneyStoreError(f"读取 Supabase 游资缓存失败：{exc}") from exc

    def save_payload(self, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return

        trade_date = _normalize_trade_date_text(payload.get("trade_date"))
        if not trade_date:
            return

        items = list(payload.get("items") or [])
        rows = [_serialize_item(trade_date, item) for item in items]

        try:
            with self._connection() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            insert into app_private.hot_money_daily_fetches (
                              trade_date, source_api, status, record_count, fetched_at, updated_at
                            )
                            values (%s, 'hm_detail', %s, %s, timezone('utc', now()), timezone('utc', now()))
                            on conflict (trade_date) do update set
                              source_api = excluded.source_api,
                              status = excluded.status,
                              record_count = excluded.record_count,
                              fetched_at = excluded.fetched_at,
                              updated_at = excluded.updated_at
                            """,
                            (trade_date, "success" if rows else "empty", len(rows)),
                        )
                        cur.execute(
                            "delete from app_private.hot_money_daily_trades where trade_date = %s",
                            (trade_date,),
                        )
                        if rows:
                            cur.executemany(
                                """
                                insert into app_private.hot_money_daily_trades (
                                  trade_date, ts_code, ts_name, buy_amount, sell_amount, net_amount,
                                  hm_name, hm_orgs, tag, raw_payload, fetched_at
                                )
                                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, timezone('utc', now()))
                                """,
                                rows,
                            )
        except HotMoneyStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise HotMoneyStoreError(f"写入 Supabase 游资缓存失败：{exc}") from exc

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def _connection(self):
        if self._disabled_until > time.time():
            raise HotMoneyStoreError("Supabase 游资缓存连接暂时熔断，等待冷却后再试。")
        pool = self._get_pool()
        return pool.connection(timeout=self.connection_timeout_seconds)

    def _get_pool(self):
        if self._pool is not None:
            return self._pool
        if not self.enabled:
            raise HotMoneyStoreError("未配置 SUPABASE_DB_URL，无法使用游资数据库缓存。")
        try:
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool
        except Exception as exc:
            raise HotMoneyStoreError("未安装 psycopg / psycopg_pool，无法启用 PostgreSQL session pool。") from exc

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
            raise HotMoneyStoreError(f"Supabase PostgreSQL session pool 初始化失败：{exc}") from exc

    def _trip_circuit(self) -> None:
        self.close()
        self._disabled_until = time.time() + self.failure_cooldown_seconds


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
