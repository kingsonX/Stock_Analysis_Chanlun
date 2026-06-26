from __future__ import annotations

from typing import Any

from .data_provider import DataProviderError, TushareClient
from .smart_picker import SmartPickerService
from .watchlist_store import AnalysisWatchlistStore, WatchlistStoreError


class WatchtowerService:
    EASTMONEY_GROUP_NAME = "重点监控"

    def __init__(
        self,
        data_client: TushareClient | None = None,
        picker_client: SmartPickerService | None = None,
        store: AnalysisWatchlistStore | None = None,
    ):
        self.data_client = data_client or TushareClient()
        self.picker_client = picker_client or SmartPickerService(data_client=self.data_client)
        self.store = store or AnalysisWatchlistStore(
            dsn=getattr(self.data_client, "_stock_basic_store", None).dsn if getattr(self.data_client, "_stock_basic_store", None) else "",
            min_size=getattr(self.data_client, "_stock_basic_store", None).min_size if getattr(self.data_client, "_stock_basic_store", None) else 1,
            max_size=getattr(self.data_client, "_stock_basic_store", None).max_size if getattr(self.data_client, "_stock_basic_store", None) else 4,
        )

    def overview(self, query: str = "", page: int = 1, page_size: int = 12) -> dict[str, Any]:
        store_error = ""
        try:
            entries = self.store.list_entries(query=query)
        except WatchlistStoreError as exc:
            entries = []
            store_error = str(exc)
        realtime_error = ""
        realtime_map: dict[str, dict[str, Any]] = {}
        if entries:
            try:
                realtime_rows = self.data_client.get_realtime_daily([item.get("ts_code", "") for item in entries])
                realtime_map = {str(item.get("ts_code") or "").strip().upper(): item for item in realtime_rows}
            except DataProviderError as exc:
                realtime_error = exc.message

        items = [self._build_watch_item(entry, realtime_map.get(entry.get("ts_code", "").upper())) for entry in entries]
        items.sort(key=_watch_sort_key)
        pager = _paginate(items, page=page, page_size=page_size)
        return {
            "status": "ok",
            "query": str(query or "").strip(),
            "page": pager["page"],
            "page_size": pager["page_size"],
            "total": pager["total"],
            "total_pages": pager["total_pages"],
            "summary": self._build_summary(items, realtime_error, store_error),
            "items": pager["items"],
            "realtime_error": realtime_error,
            "store_error": store_error,
        }

    def track_stock(self, stock: dict[str, Any], bak_basic: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.store.enabled:
            return {"status": "disabled", "message": "未配置 MySQL 智能盯盘数据库。"}
        try:
            self.store.save_entry(stock=stock, bak_basic=bak_basic)
        except WatchlistStoreError as exc:
            return {"status": "error", "message": str(exc)}
        return {"status": "ok", "message": "智能盯盘数据库已更新。"}

    def delete_stock(self, ts_code: str) -> dict[str, Any]:
        if not self.store.enabled:
            raise DataProviderError("未配置 MySQL 智能盯盘数据库。", 500)
        try:
            entry = self.store.get_entry(ts_code)
        except WatchlistStoreError as exc:
            raise DataProviderError(str(exc), 503) from exc
        if not entry:
            raise DataProviderError("数据库里没有找到这只自选股。", 404)
        target = entry.get("ts_code") or entry.get("symbol") or entry.get("name") or ts_code
        self.picker_client.manage_watchlist(action="delete", target=target)
        try:
            deleted = self.store.delete_entry(entry.get("ts_code", ""))
        except WatchlistStoreError as exc:
            raise DataProviderError(str(exc), 503) from exc
        return {
            "status": "ok",
            "deleted": deleted,
            "stock": {
                "ts_code": entry.get("ts_code", ""),
                "symbol": entry.get("symbol", ""),
                "name": entry.get("name", ""),
            },
            "message": "已从自选和智能盯盘数据库移除。",
        }

    def realtime_detail(self, ts_code: str) -> dict[str, Any]:
        if not self.store.enabled:
            raise DataProviderError("未配置 MySQL 智能盯盘数据库。", 500)
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            raise DataProviderError("缺少股票代码。", 400)
        try:
            entry = self.store.get_entry(cleaned_code)
        except WatchlistStoreError as exc:
            raise DataProviderError(str(exc), 503) from exc
        if not entry:
            raise DataProviderError("数据库里没有找到这只股票。", 404)

        realtime_error = ""
        realtime_row: dict[str, Any] | None = None
        try:
            rows = self.data_client.get_realtime_daily(cleaned_code)
            realtime_row = rows[0] if rows else None
        except DataProviderError as exc:
            realtime_error = exc.message

        watch_item = self._build_watch_item(entry, realtime_row)
        return {
            "status": "ok",
            "stock": watch_item["stock"],
            "cache": watch_item["cache"],
            "realtime": watch_item["realtime"],
            "yangjia": watch_item["yangjia"],
            "realtime_error": realtime_error,
        }

    def add_to_eastmoney_group(self, ts_code: str, group_name: str | None = None) -> dict[str, Any]:
        if not self.store.enabled:
            raise DataProviderError("未配置 MySQL 智能盯盘数据库。", 500)
        cleaned_code = str(ts_code or "").strip().upper()
        if not cleaned_code:
            raise DataProviderError("缺少股票代码。", 400)
        try:
            entry = self.store.get_entry(cleaned_code)
        except WatchlistStoreError as exc:
            raise DataProviderError(str(exc), 503) from exc
        if not entry:
            raise DataProviderError("数据库里没有找到这只股票。", 404)

        group = str(group_name or self.EASTMONEY_GROUP_NAME).strip() or self.EASTMONEY_GROUP_NAME
        stock = dict(entry.get("stock") or {})
        target = stock.get("ts_code") or stock.get("symbol") or stock.get("name") or cleaned_code
        result = self.picker_client.manage_watchlist_group(action="add", target=str(target), group_name=group)
        return {
            "status": "ok",
            "group_name": group,
            "stock": {
                "ts_code": stock.get("ts_code", cleaned_code),
                "symbol": stock.get("symbol", ""),
                "name": stock.get("name", ""),
            },
            "message": f"{stock.get('name') or cleaned_code} 已加入东方财富自选组“{group}”。",
            "eastmoney": result,
        }

    def _build_summary(self, items: list[dict[str, Any]], realtime_error: str = "", store_error: str = "") -> dict[str, Any]:
        strong_count = sum(1 for item in items if item.get("yangjia", {}).get("label") == "主流先手")
        absorb_count = sum(1 for item in items if item.get("yangjia", {}).get("label") == "分歧承接")
        risk_count = sum(1 for item in items if item.get("yangjia", {}).get("label") == "兑现回避")
        total = len(items)
        if store_error:
            headline = "智能盯盘数据库暂时不可用，先别急着操作。"
            action = "等数据库缓存恢复后，再看自选与实时日线。"
        elif realtime_error:
            headline = "实时日线暂时没拉回来，先看数据库里的自选底仓。"
            action = "先排查 `rt_k` 权限，再看盘。"
        elif strong_count + absorb_count >= max(1, risk_count):
            headline = "今天先盯强承接和主流先手，后排别追。"
            action = "先看红盘强承接，再看分歧后谁能扛住。"
        else:
            headline = "兑现和回落样本偏多，先收缩关注面。"
            action = "只看最强，弱的先删掉观察。"
        return {
            "total": total,
            "strong_count": strong_count,
            "absorb_count": absorb_count,
            "risk_count": risk_count,
            "headline": headline,
            "action": action,
            "realtime_error": realtime_error,
            "store_error": store_error,
        }

    def _build_watch_item(self, entry: dict[str, Any], realtime_row: dict[str, Any] | None) -> dict[str, Any]:
        stock = dict(entry.get("stock") or {})
        cache = dict(entry.get("bak_basic") or {})
        realtime = _normalize_realtime_row(realtime_row or {})
        yangjia = _build_yangjia_view(stock=stock, cache=cache, realtime=realtime)
        return {
            "stock": stock,
            "cache": cache,
            "realtime": realtime,
            "yangjia": yangjia,
            "updated_at": entry.get("updated_at", ""),
        }


def _normalize_realtime_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row or {})
    pre_close = _as_float(normalized.get("pre_close"))
    open_price = _as_float(normalized.get("open"))
    high_price = _as_float(normalized.get("high"))
    low_price = _as_float(normalized.get("low"))
    close_price = _as_float(normalized.get("close"))
    amount = _as_float(normalized.get("amount"))
    vol = _as_float(normalized.get("vol"))
    num = _as_float(normalized.get("num"))
    day_pct = ((close_price - pre_close) / pre_close * 100) if pre_close else 0.0
    open_pct = ((open_price - pre_close) / pre_close * 100) if pre_close else 0.0
    amplitude_pct = ((high_price - low_price) / pre_close * 100) if pre_close else 0.0
    close_position = ((close_price - low_price) / (high_price - low_price)) if high_price > low_price else 0.5
    return {
        "ts_code": str(normalized.get("ts_code") or "").strip().upper(),
        "name": str(normalized.get("name") or "").strip(),
        "pre_close": pre_close,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "vol": vol,
        "amount": amount,
        "num": num,
        "ask_price1": _as_float(normalized.get("ask_price1")),
        "ask_volume1": _as_float(normalized.get("ask_volume1")),
        "bid_price1": _as_float(normalized.get("bid_price1")),
        "bid_volume1": _as_float(normalized.get("bid_volume1")),
        "trade_time": str(normalized.get("trade_time") or "").strip(),
        "day_pct": day_pct,
        "open_pct": open_pct,
        "amplitude_pct": amplitude_pct,
        "close_position": close_position,
    }


def _build_yangjia_view(stock: dict[str, Any], cache: dict[str, Any], realtime: dict[str, Any]) -> dict[str, Any]:
    name = stock.get("name") or stock.get("symbol") or stock.get("ts_code") or "这只票"
    industry = stock.get("industry") or cache.get("industry") or "未知方向"
    if not realtime or not realtime.get("pre_close"):
        return {
            "label": "待补实时",
            "tone": "neutral",
            "action": "先看资料，不急着下判断。",
            "summary": f"{name} 的实时日线暂时没拿到，先把它当成 {industry} 方向的观察样本。",
            "basis": [
                f"行业归属：{industry}",
                f"数据库快照日期：{cache.get('trade_date') or '未知'}",
            ],
            "risk": "缺少实时承接数据时，不做追价判断。",
        }

    day_pct = float(realtime.get("day_pct") or 0)
    open_pct = float(realtime.get("open_pct") or 0)
    amplitude_pct = float(realtime.get("amplitude_pct") or 0)
    close_position = float(realtime.get("close_position") or 0)
    amount = float(realtime.get("amount") or 0)
    capacity_ok = amount >= 800000000

    if day_pct >= 1.5 and close_position >= 0.68 and capacity_ok:
        label = "主流先手"
        tone = "positive"
        action = "先盯前排，不追后排。"
        summary = f"{name} 日内强于昨收，收在高位附近，像养家会先看一眼的前排强票。"
        risk = "如果高位放量后回落到日内中下沿，说明先手优势在钝化。"
    elif day_pct >= 0 and amplitude_pct >= 3.5 and close_position >= 0.52:
        label = "分歧承接"
        tone = "positive"
        action = "看分歧后的承接，等确认再动。"
        summary = f"{name} 盘中有分歧，但回收还可以，更像承接观察，不像纯兑现。"
        risk = "如果尾盘重新压回日低附近，这种分歧承接就容易变成假动作。"
    elif day_pct <= -2 or close_position <= 0.24:
        label = "兑现回避"
        tone = "caution"
        action = "先回避，别替市场接刀。"
        summary = f"{name} 收盘位置偏弱，日内更像兑现和退潮，不是养家喜欢硬接的那种票。"
        risk = "弱势票第二天再低开，容易继续放大亏钱效应。"
    else:
        label = "轮动观察"
        tone = "neutral"
        action = "只看，不追，不臆测它会自动走成龙头。"
        summary = f"{name} 今天强弱一般，先放在轮动观察位，等主流和承接都更清楚。"
        risk = "如果没有新的量能和辨识度，它很容易沦为跟风。"

    return {
        "label": label,
        "tone": tone,
        "action": action,
        "summary": summary,
        "basis": [
            f"开盘强弱：{open_pct:+.2f}%",
            f"实时涨幅：{day_pct:+.2f}%",
            f"振幅：{amplitude_pct:.2f}%",
            f"成交额：{_format_amount_short(amount)}",
            f"行业：{industry}",
        ],
        "risk": risk,
    }


def _paginate(items: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    safe_page_size = max(1, int(page_size or 1))
    total = len(items)
    total_pages = max(1, (total + safe_page_size - 1) // safe_page_size)
    current_page = min(max(int(page or 1), 1), total_pages)
    start = (current_page - 1) * safe_page_size
    return {
        "items": items[start : start + safe_page_size],
        "page": current_page,
        "page_size": safe_page_size,
        "total": total,
        "total_pages": total_pages,
    }


def _watch_sort_key(item: dict[str, Any]) -> tuple[float, float, str]:
    realtime = item.get("realtime") or {}
    yangjia = item.get("yangjia") or {}
    tone_weight = {"positive": 0, "neutral": 1, "caution": 2}.get(yangjia.get("tone"), 3)
    return (
        tone_weight,
        -(abs(float(realtime.get("day_pct") or 0))),
        str(item.get("stock", {}).get("ts_code") or ""),
    )


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _format_amount_short(amount: float) -> str:
    value = float(amount or 0)
    if abs(value) >= 100000000:
        return f"{value / 100000000:.2f}亿"
    if abs(value) >= 10000:
        return f"{value / 10000:.0f}万"
    return f"{value:.0f}"
