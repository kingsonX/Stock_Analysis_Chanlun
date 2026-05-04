from __future__ import annotations

from typing import Any

from .chanlun import analyze_klines
from .config import LEVELS, default_date_range
from .data_provider import DataProviderError, TushareClient
from .mx_provider import MXDataProvider, MXProviderError
from .trading_profile import (
    MXBaseClient,
    MXNewsProvider,
    MXScreenProvider,
    TradingProfileService,
    _build_column_map,
    _columns_order,
    _datalist_to_rows,
    _flatten,
    _latest_signal,
    _parse_partial_results_table,
    _safe_int,
    _signal_short_label,
)


class MXWatchlistProvider(MXBaseClient):
    QUERY_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/get"
    MANAGE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/manage"

    def query(self) -> dict[str, Any]:
        result = self._post_json(self.QUERY_URL, {})
        status = result.get("status")
        code = result.get("code")
        if status not in (0, "0", None) and code not in (0, "0", None):
            raise MXProviderError(f"自选股查询失败：{result.get('message') or status or code}", 502)

        data = result.get("data", {})
        inner = data.get("allResults", {}).get("result", {}) if isinstance(data, dict) else {}
        columns = inner.get("columns", []) if isinstance(inner, dict) else []
        data_list = inner.get("dataList", []) if isinstance(inner, dict) else []
        rows = _datalist_to_rows(data_list, _build_column_map(columns), _columns_order(columns))

        items = []
        for row in rows:
            code_text = _row_value(row, ["股票代码", "代码"])
            name_text = _row_value(row, ["股票名称", "名称"]) or _row_value(row, ["股票简称", "名称"])
            items.append(
                {
                    "code": code_text,
                    "name": name_text,
                    "latest_price": _row_value(row, ["最新价"]),
                    "change_pct": _row_value(row, ["涨跌幅"]),
                    "turnover": _row_value(row, ["换手率"]),
                    "volume_ratio": _row_value(row, ["量比"]),
                    "raw": row,
                }
            )

        return {
            "status": "ok" if items else "empty",
            "label": "我的自选",
            "items": items,
            "total": len(items),
        }

    def manage(self, action: str, target: str) -> dict[str, Any]:
        cleaned_action = (action or "").strip().lower()
        cleaned_target = (target or "").strip()
        if cleaned_action not in {"add", "delete"}:
            raise MXProviderError("自选操作只支持 add 或 delete。", 400)
        if not cleaned_target:
            raise MXProviderError("缺少自选股代码或名称。", 400)

        if cleaned_action == "add":
            query = f"把{cleaned_target}添加到我的自选股列表"
        else:
            query = f"把{cleaned_target}从我的自选股列表删除"

        result = self._post_json(self.MANAGE_URL, {"query": query})
        status = result.get("status")
        code = result.get("code")
        if status not in (0, "0", None) and code not in (0, "0", None):
            raise MXProviderError(f"自选操作失败：{result.get('message') or status or code}", 502)

        return {
            "status": "ok",
            "action": cleaned_action,
            "target": cleaned_target,
            "message": _flatten(result.get("message") or "操作成功"),
        }


class SmartPickerService:
    def __init__(
        self,
        data_client: TushareClient | None = None,
        mx_data_provider: MXDataProvider | None = None,
        news_provider: MXNewsProvider | None = None,
        screen_provider: MXScreenProvider | None = None,
        watchlist_provider: MXWatchlistProvider | None = None,
        trading_profile: TradingProfileService | None = None,
    ):
        self.data_client = data_client or TushareClient()
        self.mx_data_provider = mx_data_provider or MXDataProvider()
        shared_key = getattr(self.mx_data_provider, "api_key", None)
        self.news_provider = news_provider or MXNewsProvider(api_key=shared_key)
        self.screen_provider = screen_provider or MXScreenProvider(api_key=shared_key)
        self.watchlist_provider = watchlist_provider or MXWatchlistProvider(api_key=shared_key)
        self.trading_profile = trading_profile or TradingProfileService(
            mx_data_provider=self.mx_data_provider,
            news_provider=self.news_provider,
            screen_provider=self.screen_provider,
        )

    def overview(self) -> dict[str, Any]:
        market_cards = [
            self._market_card("market_heat", "高涨幅热度", "今日涨幅大于5%的A股"),
            self._market_card("market_liquidity", "活跃成交", "成交额大于10亿的A股"),
            self._market_card("market_pressure", "下跌承压", "今日跌幅大于5%的A股"),
        ]
        news = self._safe_news("A股 今日 主流板块 政策 催化 最新公告")
        stage = _market_stage(market_cards)
        return {
            "status": "ok",
            "stage": stage,
            "universe": self._universe(),
            "market_cards": market_cards,
            "news": news,
        }

    def screen(self, query_text: str, level: str = "daily", limit: int = 20) -> dict[str, Any]:
        cleaned_query = (query_text or "").strip()
        if not cleaned_query:
            raise MXProviderError("请输入智能选股条件。", 400)
        if level not in LEVELS:
            raise MXProviderError(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        parsed = self.screen_provider.parse_response(self.screen_provider.search(cleaned_query))
        stage = _market_stage(
            [
                self._market_card("market_heat", "高涨幅热度", "今日涨幅大于5%的A股"),
                self._market_card("market_liquidity", "活跃成交", "成交额大于10亿的A股"),
                self._market_card("market_pressure", "下跌承压", "今日跌幅大于5%的A股"),
            ]
        )

        candidates = []
        errors = []
        for row in parsed.get("rows", [])[:limit]:
            try:
                candidates.append(self._candidate_from_row(row, level, stage))
            except (DataProviderError, MXProviderError) as exc:
                errors.append({"row": row, "message": getattr(exc, "message", str(exc))})

        return {
            "status": "ok",
            "query_text": cleaned_query,
            "level": level,
            "level_label": LEVELS[level]["label"],
            "universe": self._universe(),
            "description": parsed.get("description", ""),
            "parser_text": parsed.get("parser_text", ""),
            "total": parsed.get("total", 0),
            "stage": stage,
            "candidates": candidates,
            "errors": errors,
        }

    def candidate_detail(self, stock: dict[str, Any], level: str = "daily") -> dict[str, Any]:
        query = _flatten(stock.get("ts_code") or stock.get("symbol") or stock.get("name")).strip()
        if not query:
            raise MXProviderError("缺少候选股代码或名称。", 400)
        if level not in LEVELS:
            raise MXProviderError(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        stock_record = self.data_client.resolve_stock(query)
        start_date, end_date = default_date_range(level)
        klines = self.data_client.get_klines(stock_record.ts_code, level, start_date, end_date)
        analysis = analyze_klines(klines, level=level)
        analysis["stock"] = stock_record.as_dict()
        analysis["query"] = {
            "level": level,
            "level_label": LEVELS[level]["label"],
            "start_date": start_date,
            "end_date": end_date,
        }
        profile = self.trading_profile.build(stock=stock_record.as_dict(), analysis=analysis)
        try:
            watchlist = self.watchlist()
            watch_codes = {item.get("code", "") for item in watchlist.get("items", [])}
            in_watchlist = stock_record.symbol in watch_codes or stock_record.ts_code.split(".")[0] in watch_codes
        except MXProviderError as exc:
            watchlist = {"status": "error", "message": exc.message, "items": [], "total": 0}
            in_watchlist = False
        return {
            "status": "ok",
            "stock": stock_record.as_dict(),
            "analysis": {
                "trend": analysis.get("trend", {}),
                "signals": analysis.get("signals", [])[-3:],
                "divergences": analysis.get("divergences", [])[-3:],
                "risk_cards": analysis.get("risk_cards", [])[-3:],
                "level_context": analysis.get("level_context", {}),
            },
            "profile": profile,
            "watchlist": {
                "status": watchlist.get("status"),
                "in_watchlist": in_watchlist,
                "total": watchlist.get("total", 0),
            },
        }

    def watchlist(self) -> dict[str, Any]:
        return self.watchlist_provider.query()

    def manage_watchlist(self, action: str, target: str) -> dict[str, Any]:
        return self.watchlist_provider.manage(action=action, target=target)

    def _universe(self) -> dict[str, Any]:
        load_stocks = getattr(self.data_client, "load_stocks", None)
        if not callable(load_stocks):
            return {"label": "全A股", "status": "empty", "total": 0, "summary": "当前环境未提供全市场股票总数。"}
        try:
            total = len(load_stocks())
        except DataProviderError as exc:
            return {"label": "全A股", "status": "error", "total": 0, "message": exc.message}
        return {
            "label": "全A股",
            "status": "ok",
            "total": total,
            "summary": f"当前可扫描 A 股股票约 {total} 只，智能选股条件默认以全市场为范围执行。",
        }

    def _market_card(self, key: str, label: str, query_text: str) -> dict[str, Any]:
        try:
            parsed = self.screen_provider.parse_response(self.screen_provider.search(query_text))
        except MXProviderError as exc:
            return {
                "key": key,
                "label": label,
                "query_text": query_text,
                "status": "error",
                "total": 0,
                "description": "",
                "parser_text": "",
                "rows": [],
                "error": exc.message,
            }

        return {
            "key": key,
            "label": label,
            "query_text": query_text,
            "status": "ok" if parsed.get("rows") or parsed.get("total") else "empty",
            "total": parsed.get("total", 0),
            "description": parsed.get("description", ""),
            "parser_text": parsed.get("parser_text", ""),
            "rows": parsed.get("rows", [])[:6],
        }

    def _safe_news(self, query_text: str) -> dict[str, Any]:
        try:
            return {
                "status": "ok",
                "query_text": query_text,
                **self.news_provider.parse_response(self.news_provider.search(query_text)),
            }
        except MXProviderError as exc:
            return {"status": "error", "message": exc.message, "items": [], "query_text": query_text}

    def _candidate_from_row(self, row: dict[str, Any], level: str, stage: dict[str, Any]) -> dict[str, Any]:
        query = (
            _row_value(row, ["股票代码", "代码"])
            or _row_value(row, ["股票简称", "名称"])
            or _row_value(row, ["股票名称", "名称"])
        )
        if not query:
            raise MXProviderError("选股结果缺少股票代码或名称。", 502)

        stock = self.data_client.resolve_stock(query)
        start_date, end_date = default_date_range(level)
        klines = self.data_client.get_klines(stock.ts_code, level, start_date, end_date)
        analysis = analyze_klines(klines, level=level)

        structure = _candidate_structure(analysis, level)
        emotion = _candidate_emotion(stage)
        capacity = _candidate_capacity(row)
        overall = _candidate_overall(structure, emotion, capacity)

        return {
            "stock": stock.as_dict(),
            "level": level,
            "level_label": LEVELS[level]["label"],
            "quote": {
                "latest_price": _row_value(row, ["最新价"]),
                "change_pct": _row_value(row, ["涨跌幅"]),
                "change_pct_value": _parse_numeric(_row_value(row, ["涨跌幅"])),
                "turnover": _row_value(row, ["换手率"]),
                "turnover_value": _parse_numeric(_row_value(row, ["换手率"])),
                "amount": _row_value(row, ["成交额", "成交金额"]),
                "amount_value": _parse_numeric(_row_value(row, ["成交额", "成交金额"])),
            },
            "structure": structure,
            "emotion": emotion,
            "capacity": capacity,
            "overall": overall,
            "screen_row": row,
        }


def _market_stage(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {item.get("key"): item for item in cards}
    rise = _safe_int((by_key.get("market_heat") or {}).get("total"))
    active = _safe_int((by_key.get("market_liquidity") or {}).get("total"))
    pressure = _safe_int((by_key.get("market_pressure") or {}).get("total"))

    score = 0
    if rise >= 80:
        score += 2
    elif rise >= 40:
        score += 1
    if active >= 160:
        score += 2
    elif active >= 80:
        score += 1
    if pressure >= 60:
        score -= 2
    elif pressure >= 30:
        score -= 1

    if score >= 3:
        label = "主流活跃"
        tone = "positive"
        action = "养家视角：赚钱效应还在，适合在主流和辨识度里选强，不适合无差别乱扫。"
    elif score >= 1:
        label = "轮动平衡"
        tone = "neutral"
        action = "养家视角：情绪不差，但强度还没到闭眼跟，先挑有结构、有承接的方向。"
    else:
        label = "情绪偏弱"
        tone = "caution"
        action = "养家视角：先看风险收益比，市场没有明显赚钱效应时，宁可少做，不要靠想象补仓。"

    return {
        "label": label,
        "tone": tone,
        "summary": f"高涨幅个股 {rise} 只，活跃成交股 {active} 只，下跌承压股 {pressure} 只。",
        "basis": [
            f"高涨幅个股：{rise} 只",
            f"活跃成交股：{active} 只",
            f"下跌承压股：{pressure} 只",
        ],
        "action": action,
    }


def _candidate_structure(analysis: dict[str, Any], level: str) -> dict[str, Any]:
    trend = analysis.get("trend") or {}
    signal = _latest_signal(analysis.get("signals") or [])
    divergence = (analysis.get("divergences") or [])[-1] if analysis.get("divergences") else None

    score = 45
    tone = "neutral"
    if trend.get("direction") == "up":
        score += 12
    elif trend.get("direction") == "down":
        score -= 12
    if trend.get("position") == "above_center":
        score += 10
    elif trend.get("position") == "below_center":
        score -= 10

    if signal and signal.get("side") == "buy":
        score += 18 if signal.get("status") == "confirmed" else 10
    elif signal and signal.get("side") == "sell":
        score -= 18 if signal.get("status") == "confirmed" else 10

    if score >= 68:
        label = "结构可看"
        tone = "positive"
    elif score >= 52:
        label = "候选观察"
    else:
        label = "结构回避"
        tone = "caution"

    return {
        "score": max(0, min(100, score)),
        "label": label,
        "tone": tone,
        "summary": f"{LEVELS[level]['label']} · {trend.get('label') or '结构不足'} · {trend.get('position_label') or '无位次'}",
        "signal": f"{_signal_short_label(signal)} {signal.get('status_label')}".strip() if signal else "暂无买卖点",
        "divergence": divergence.get("label") if divergence else "",
        "invalidation_price": signal.get("invalidation_price") if signal else None,
    }


def _candidate_emotion(stage: dict[str, Any]) -> dict[str, Any]:
    label = stage.get("label") or "情绪未明"
    tone = stage.get("tone") or "neutral"
    score = 74 if tone == "positive" else 56 if tone == "neutral" else 38
    return {
        "score": score,
        "label": label,
        "tone": tone,
        "summary": stage.get("summary") or "",
    }


def _candidate_capacity(row: dict[str, Any]) -> dict[str, Any]:
    turnover_text = _row_value(row, ["换手率"])
    amount_text = _row_value(row, ["成交额", "成交金额"])
    change_text = _row_value(row, ["涨跌幅"])

    turnover = _parse_numeric(turnover_text)
    amount = _parse_numeric(amount_text)
    change_pct = _parse_numeric(change_text)

    score = 45
    tone = "neutral"
    if amount >= 3_000_000_000:
        score += 22
    elif amount >= 1_000_000_000:
        score += 14
    elif amount > 0:
        score += 4
    else:
        score -= 8

    if 3 <= turnover <= 18:
        score += 14
    elif turnover > 18:
        score += 6
    elif turnover > 0:
        score -= 4

    if change_pct >= 5:
        score += 6

    if score >= 70:
        label = "容量较优"
        tone = "positive"
    elif score >= 54:
        label = "容量中等"
    else:
        label = "容量待核"
        tone = "caution"

    return {
        "score": max(0, min(100, score)),
        "label": label,
        "tone": tone,
        "summary": f"成交额 {amount_text or '-'} · 换手率 {turnover_text or '-'}",
    }


def _candidate_overall(structure: dict[str, Any], emotion: dict[str, Any], capacity: dict[str, Any]) -> dict[str, Any]:
    score = round(structure.get("score", 0) * 0.5 + emotion.get("score", 0) * 0.25 + capacity.get("score", 0) * 0.25)
    if structure.get("tone") == "caution":
        label = "暂不参与"
        tone = "caution"
        decision = "结构没站稳时，不把热度和容量当买入理由。"
    elif score >= 72 and emotion.get("tone") != "caution":
        label = "重点观察"
        tone = "positive"
        decision = "结构、环境和容量有一定共振，可以进入重点观察池，但仍要等确认。"
    elif score >= 58:
        label = "候选观察"
        tone = "neutral"
        decision = "有一定可看点，适合列入候选池，等结构确认或环境强化。"
    else:
        label = "暂不参与"
        tone = "caution"
        decision = "强度不够整齐，先观察，不急着把它升级成交易对象。"
    return {"score": score, "label": label, "tone": tone, "decision": decision}


def _row_value(row: dict[str, Any], keywords: list[str]) -> str:
    if not isinstance(row, dict):
        return ""
    for key, value in row.items():
        key_text = _flatten(key)
        if any(keyword in key_text for keyword in keywords):
            return _flatten(value)
    return ""


def _parse_numeric(value: Any) -> float:
    text = _flatten(value).replace(",", "").replace("，", "").strip()
    if not text:
        return 0.0

    unit = 1.0
    if "万亿" in text:
        unit = 1_0000_0000_0000.0
    elif "亿" in text:
        unit = 100_000_000.0
    elif "万" in text:
        unit = 10_000.0

    cleaned = []
    for ch in text:
        if ch.isdigit() or ch in ".-":
            cleaned.append(ch)
    try:
        return float("".join(cleaned)) * unit if cleaned else 0.0
    except ValueError:
        return 0.0
