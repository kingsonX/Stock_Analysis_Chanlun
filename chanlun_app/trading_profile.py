from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from .mx_provider import MXDataProvider, MXProviderError, _env_value


class MXBaseClient:
    def __init__(self, api_key: str | None = None, timeout_seconds: int = 20):
        self.api_key = api_key or _env_value("MX_APIKEY")
        self.timeout_seconds = timeout_seconds

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise MXProviderError("缺少 MX_APIKEY 环境变量，请先在服务端配置妙想金融数据 API Key。", 500)

        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "apikey": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise MXProviderError(f"MX 数据请求失败：HTTP {exc.code}", 502) from exc
        except urllib.error.URLError as exc:
            raise MXProviderError(f"MX 数据网络访问失败：{exc.reason}", 502) from exc
        except TimeoutError as exc:
            raise MXProviderError("MX 数据请求超时。", 504) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MXProviderError("MX 数据返回内容不是有效 JSON。", 502) from exc


class MXNewsProvider(MXBaseClient):
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search"

    def search(self, query: str) -> dict[str, Any]:
        return self._post_json(self.BASE_URL, {"query": query})

    def digest(self, target: str) -> dict[str, Any]:
        query_text = f"{target} 最新公告 研报 机构观点"
        parsed = self.parse_response(self.search(query_text))
        return {
            "status": "ok" if parsed["items"] else "empty",
            "label": "资讯催化",
            "query_text": query_text,
            **parsed,
        }

    @staticmethod
    def parse_response(result: dict[str, Any]) -> dict[str, Any]:
        status = result.get("status")
        if status not in (0, "0", None):
            raise MXProviderError(f"MX 资讯返回错误：{result.get('message') or status}", 502)

        items = (
            result.get("data", {})
            .get("data", {})
            .get("llmSearchResponse", {})
            .get("data", [])
        )
        normalized = []
        for item in items[:6]:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "title": _flatten(item.get("title") or "无标题"),
                    "date": _flatten(item.get("date") or ""),
                    "source": _flatten(item.get("insName") or item.get("source") or ""),
                    "type": _news_type(item.get("informationType")),
                    "entity_name": _flatten(item.get("entityFullName") or ""),
                    "summary": _short_text(item.get("content") or item.get("trunk") or item.get("summary") or ""),
                }
            )
        return {"items": normalized, "total": len(normalized)}


class MXScreenProvider(MXBaseClient):
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/stock-screen"

    def search(self, keyword: str) -> dict[str, Any]:
        return self._post_json(self.BASE_URL, {"keyword": keyword})

    def scan(self, stock_name: str, industry: str, symbol: str = "") -> dict[str, Any]:
        cards = [
            self._card("market_heat", "市场热度", "今日涨幅大于5%的A股", symbol, stock_name),
            self._card("market_liquidity", "成交活跃", "成交额大于10亿的A股", symbol, stock_name),
        ]
        if industry:
            cards.append(self._card("industry_strength", "行业强度", f"{industry}行业涨幅大于2%的股票", symbol, stock_name))
        else:
            cards.append(
                {
                    "key": "industry_strength",
                    "label": "行业强度",
                    "query_text": "",
                    "status": "empty",
                    "error": "当前股票缺少行业信息，无法做行业扫描。",
                    "total": 0,
                    "rows": [],
                    "parser_text": "",
                    "description": "",
                    "hit_current_stock": False,
                }
            )

        return {"status": "ok", "label": "市场扫描", "industry": industry, "cards": cards}

    def _card(self, key: str, label: str, query_text: str, symbol: str, stock_name: str) -> dict[str, Any]:
        try:
            parsed = self.parse_response(self.search(query_text))
        except MXProviderError as exc:
            return {
                "key": key,
                "label": label,
                "query_text": query_text,
                "status": "error",
                "error": exc.message,
                "total": 0,
                "rows": [],
                "parser_text": "",
                "description": "",
                "hit_current_stock": False,
            }

        hit = any(_scan_matches_current(row, symbol, stock_name) for row in parsed["rows"])
        return {
            "key": key,
            "label": label,
            "query_text": query_text,
            "status": "ok" if parsed["rows"] or parsed["total"] else "empty",
            "total": parsed["total"],
            "rows": parsed["rows"][:6],
            "parser_text": parsed["parser_text"],
            "description": parsed["description"],
            "hit_current_stock": hit,
        }

    @staticmethod
    def parse_response(result: dict[str, Any]) -> dict[str, Any]:
        status = result.get("status")
        if status not in (0, "0", None):
            raise MXProviderError(f"MX 选股返回错误：{result.get('message') or status}", 502)

        data = result.get("data", {})
        inner = data.get("data", {})
        all_result = inner.get("allResults", {}).get("result", {})
        columns = all_result.get("columns", [])
        datalist = all_result.get("dataList", [])
        rows = []
        if isinstance(datalist, list) and datalist:
            rows = _datalist_to_rows(datalist, _build_column_map(columns), _columns_order(columns))
        elif inner.get("partialResults"):
            rows = _parse_partial_results_table(inner.get("partialResults", ""))

        total = _safe_int(
            all_result.get("total")
            or all_result.get("totalRecordCount")
            or inner.get("result", {}).get("total")
            or len(rows)
        )
        total_condition = inner.get("totalCondition", {})
        description = _flatten(total_condition.get("describe") or "") if isinstance(total_condition, dict) else _flatten(total_condition)
        parser_text = _flatten(inner.get("parserText") or "")
        return {"rows": rows, "total": total, "description": description, "parser_text": parser_text}


class TradingProfileService:
    def __init__(
        self,
        mx_data_provider: MXDataProvider | None = None,
        news_provider: MXNewsProvider | None = None,
        screen_provider: MXScreenProvider | None = None,
    ):
        self.mx_data_provider = mx_data_provider or MXDataProvider()
        shared_key = getattr(self.mx_data_provider, "api_key", None)
        self.news_provider = news_provider or MXNewsProvider(api_key=shared_key)
        self.screen_provider = screen_provider or MXScreenProvider(api_key=shared_key)

    def build(self, stock: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        stock = stock or {}
        analysis = analysis or {}
        name = _flatten(stock.get("name") or "")
        symbol = _flatten(stock.get("symbol") or "")
        ts_code = _flatten(stock.get("ts_code") or "")
        industry = _flatten(stock.get("industry") or "")
        target = name or ts_code or symbol
        if not target:
            raise MXProviderError("缺少股票名称或代码，无法生成交易画像。", 400)

        mx_summary = self._safe_external_call(self.mx_data_provider.summary, ts_code=ts_code, name=name)
        news = self._safe_external_call(self.news_provider.digest, target=target)
        market_scan = self._safe_external_call(self.screen_provider.scan, stock_name=target, industry=industry, symbol=symbol)

        profile = _compose_profile(stock, analysis, mx_summary, news, market_scan)
        return {
            "stock": stock,
            "profile": profile,
            "mx_summary": mx_summary,
            "news": news,
            "market_scan": market_scan,
        }

    @staticmethod
    def _safe_external_call(func, **kwargs) -> dict[str, Any]:
        try:
            data = func(**kwargs)
            if isinstance(data, dict) and "status" in data:
                return data
            return {"status": "ok", "data": data}
        except MXProviderError as exc:
            return {"status": "error", "message": exc.message}


def _compose_profile(
    stock: dict[str, Any],
    analysis: dict[str, Any],
    mx_summary: dict[str, Any],
    news: dict[str, Any],
    market_scan: dict[str, Any],
) -> dict[str, Any]:
    structure = _structure_summary(analysis)
    emotion = _emotion_summary(stock, news, market_scan)
    capacity = _capacity_summary(mx_summary)
    risk = _risk_summary(analysis, news)
    total_score = structure["score"] + emotion["score"] + capacity["score"] - risk["penalty"]
    stance, stance_label = _stance_label(total_score, structure["score"])

    conclusion = _conclusion_text(structure, emotion, capacity, risk, analysis)
    return {
        "stance": stance,
        "stance_label": stance_label,
        "headline": _headline_text(structure, emotion, capacity, risk),
        "conclusion": conclusion,
        "tags": [item for item in [structure["label"], emotion["label"], capacity["label"], risk["label"]] if item],
        "structure": structure,
        "emotion": emotion,
        "capacity": capacity,
        "risk": risk,
        "news_points": [item["title"] for item in news.get("items", [])[:3]] if news.get("status") == "ok" else [],
        "scan_points": [item["label"] for item in market_scan.get("cards", []) if item.get("status") == "ok"],
    }


def _structure_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    trend = analysis.get("trend") or {}
    query = analysis.get("query") or {}
    signals = analysis.get("signals") or []
    divergences = analysis.get("divergences") or []
    signal = _latest_signal(signals)
    divergence = divergences[-1] if divergences else None

    score = 0
    if trend.get("direction") == "up":
        score += 1
    elif trend.get("direction") == "down":
        score -= 1
    if trend.get("position") == "above_center":
        score += 1
    elif trend.get("position") == "below_center":
        score -= 1

    signal_text = "暂无最新买卖点"
    if signal:
        signal_text = f"{_signal_short_label(signal)} {signal.get('status_label') or ''}".strip()
        if signal.get("side") == "buy":
            score += 2 if signal.get("status") == "confirmed" else 1
        elif signal.get("side") == "sell":
            score -= 2 if signal.get("status") == "confirmed" else 1
        if signal.get("status") == "invalid":
            score += -1 if signal.get("side") == "buy" else 1

    if score >= 2:
        label = "结构偏多"
    elif score <= -2:
        label = "结构偏空"
    else:
        label = "结构观察"

    reason = trend.get("reason") or "当前结构仍在演化。"
    if divergence:
        reason = f"{reason} 最近背驰：{divergence.get('label') or '无'}。"
    return {
        "label": label,
        "score": score,
        "title": "缠论结构",
        "summary": f"{query.get('level_label') or analysis.get('level') or '当前级别'} · {trend.get('label') or '结构不足'} · {signal_text}",
        "detail": reason,
        "invalidation_price": signal.get("invalidation_price") if signal else None,
    }


def _emotion_summary(stock: dict[str, Any], news: dict[str, Any], market_scan: dict[str, Any]) -> dict[str, Any]:
    cards = {item.get("key"): item for item in market_scan.get("cards", []) if isinstance(item, dict)}
    market_heat = cards.get("market_heat", {})
    liquidity = cards.get("market_liquidity", {})
    industry = cards.get("industry_strength", {})
    market_total = _safe_int(market_heat.get("total"))
    liquidity_total = _safe_int(liquidity.get("total"))
    industry_total = _safe_int(industry.get("total"))
    hit_current_stock = bool(industry.get("hit_current_stock"))
    recent_news = news.get("items", [])[:3] if news.get("status") == "ok" else []

    score = 0
    if market_total >= 80:
        score += 1
    elif market_total <= 20 and market_heat.get("status") == "ok":
        score -= 1
    if industry_total >= 8:
        score += 1
    elif industry_total == 0 and industry.get("status") == "ok":
        score -= 1
    if hit_current_stock:
        score += 1
    if recent_news:
        score += 1

    if score >= 3:
        label = "主流活跃"
    elif score >= 1:
        label = "轮动可看"
    else:
        label = "情绪一般"

    industry_name = _flatten(stock.get("industry") or "所属行业")
    summary = f"高涨幅个股 {market_total} 只，活跃成交股 {liquidity_total} 只，{industry_name} 活跃股 {industry_total} 只。"
    if hit_current_stock:
        summary = f"{summary} 当前标的出现在行业活跃扫描中。"

    detail = "养家视角先看赚钱效应与主流度。"
    if recent_news:
        detail = f"{detail} 近期有资讯催化：{recent_news[0].get('title', '')}"

    return {
        "label": label,
        "score": score,
        "title": "情绪与主流",
        "summary": summary,
        "detail": detail,
    }


def _capacity_summary(mx_summary: dict[str, Any]) -> dict[str, Any]:
    if mx_summary.get("status") != "ok":
        return {
            "label": "容量未知",
            "score": 0,
            "title": "容量与资金",
            "summary": mx_summary.get("message") or "妙想行情数据暂不可用。",
            "detail": "章建平视角会先看成交承接、换手和市值容量。",
        }

    data = mx_summary.get("data", {})
    quote = data.get("quote", {})
    valuation = data.get("valuation", {})
    fund_flow = data.get("fund_flow", {})

    turnover = _metric_numeric(quote, ["换手率"])
    amount = _metric_numeric(quote, ["成交额", "成交金额"])
    market_cap = _metric_numeric(valuation, ["总市值"])
    fund_flow_value = _metric_numeric(fund_flow, ["主力净流入", "主力资金净流入", "主力净额"])

    score = 0
    if amount >= 3_000_000_000 or market_cap >= 50_000_000_000:
        score += 2
        label = "容量充足"
    elif amount >= 1_000_000_000 or market_cap >= 10_000_000_000:
        score += 1
        label = "容量中等"
    else:
        label = "容量偏小"
        score -= 1 if amount > 0 or market_cap > 0 else 0

    if turnover >= 12:
        score += 0
    elif 3 <= turnover < 12:
        score += 1
    elif turnover > 0:
        score -= 1

    if fund_flow_value > 0:
        score += 1
    elif fund_flow_value < 0:
        score -= 1

    amount_text = _metric_display(quote, ["成交额", "成交金额"])
    turnover_text = _metric_display(quote, ["换手率"])
    market_cap_text = _metric_display(valuation, ["总市值"])
    fund_flow_text = _metric_display(fund_flow, ["主力净流入", "主力资金净流入", "主力净额"])

    summary = f"成交额 {amount_text or '-'}，换手 {turnover_text or '-'}，总市值 {market_cap_text or '-'}。"
    detail = f"资金侧主力净额 {fund_flow_text or '-'}，更适合按容量和承接来理解，而不是只看形态。"
    return {"label": label, "score": score, "title": "容量与资金", "summary": summary, "detail": detail}


def _risk_summary(analysis: dict[str, Any], news: dict[str, Any]) -> dict[str, Any]:
    risk_words = ("减持", "问询", "处罚", "监管", "风险提示", "亏损", "诉讼", "质押", "解禁", "终止", "退市")
    safe_words = ("暂无", "无明显", "未见", "没有")
    hits = []
    for item in news.get("items", []) if news.get("status") == "ok" else []:
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        if any(word in text for word in risk_words) and not any(word in text for word in safe_words):
            hits.append(item.get("title") or item.get("summary") or "")

    signals = analysis.get("signals") or []
    signal = _latest_signal(signals)
    invalidation = signal.get("invalidation_price") if signal else None
    penalty = 2 if hits else 0
    if signal and signal.get("status") == "candidate":
        penalty += 1

    label = "风险可控" if penalty == 0 else "风险需盯" if penalty <= 2 else "风险偏高"
    summary = "目前未检出明显公告型风险关键词。"
    if hits:
        summary = f"资讯里出现风险词：{hits[0]}"
    if invalidation is not None:
        summary = f"{summary} 当前结构失效价 {invalidation:.3f}。"

    detail = "章建平视角会把锁定、监管、减持和流动性一起看。"
    return {"label": label, "penalty": penalty, "title": "风险边界", "summary": summary, "detail": detail}


def _stance_label(total_score: int, structure_score: int) -> tuple[str, str]:
    if structure_score <= 0 and total_score > 0:
        return "neutral", "先观察"
    if total_score >= 4:
        return "positive", "结构与环境共振"
    if total_score >= 1:
        return "positive", "结构可看"
    if total_score <= -2:
        return "caution", "风险优先"
    return "neutral", "先观察"


def _headline_text(structure: dict[str, Any], emotion: dict[str, Any], capacity: dict[str, Any], risk: dict[str, Any]) -> str:
    return f"{structure['label']}，{emotion['label']}，{capacity['label']}，{risk['label']}。"


def _conclusion_text(
    structure: dict[str, Any],
    emotion: dict[str, Any],
    capacity: dict[str, Any],
    risk: dict[str, Any],
    analysis: dict[str, Any],
) -> str:
    signal = _latest_signal(analysis.get("signals") or [])
    if signal and signal.get("side") == "buy" and structure["score"] >= 2 and emotion["score"] >= 1:
        return "结构上已经出现偏多线索，但是否值得做，要看主流和承接是否继续共振，先按失效价管理。"
    if signal and signal.get("side") == "buy":
        return "结构有点，但环境或容量没有完全配合，按候选观察，不宜把技术点当成环境确认。"
    if signal and signal.get("side") == "sell":
        return "结构转弱信号已经出现，若后续情绪和资金不能修复，优先按风险纪律而不是主观期待处理。"
    if risk["penalty"] >= 2:
        return "当前更重要的是把风险边界看清，再谈结构延续，先别让辅助信息盖过风险事实。"
    return "暂时没有特别突出的结构共振，先看主线、量能和后续公告催化，再决定是否进入观察名单。"


def _latest_signal(signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not signals:
        return None
    active = [item for item in signals if item.get("status") != "invalid"]
    return (active or signals)[-1]


def _signal_short_label(signal: dict[str, Any]) -> str:
    signal_type = _flatten(signal.get("type") or "")
    side = "卖" if signal.get("side") == "sell" else "买"
    if "三类" in signal_type:
        return f"{side}3"
    if "二类" in signal_type:
        return f"{side}2"
    if "一类" in signal_type:
        return f"{side}1"
    return side


def _metric_numeric(card: dict[str, Any], keywords: list[str]) -> float:
    return _parse_numeric(_metric_display(card, keywords))


def _metric_display(card: dict[str, Any], keywords: list[str]) -> str:
    rows = card.get("rows", []) if isinstance(card, dict) else []
    columns = card.get("columns", []) if isinstance(card, dict) else []
    if not rows or not columns:
        return ""
    row = rows[0]
    for column in columns:
        column_text = _flatten(column)
        if any(keyword in column_text for keyword in keywords):
            return _flatten(row.get(column))
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
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(cleaned) * unit if cleaned else 0.0
    except ValueError:
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _scan_matches_current(row: dict[str, Any], symbol: str, stock_name: str) -> bool:
    symbol = _flatten(symbol)
    stock_name = _flatten(stock_name)
    haystack = " ".join(_flatten(value) for value in row.values())
    return bool(symbol and symbol in haystack) or bool(stock_name and stock_name in haystack)


def _build_column_map(columns: list[dict[str, Any]]) -> dict[str, str]:
    name_map: dict[str, str] = {}
    for column in columns or []:
        if not isinstance(column, dict):
            continue
        key = _flatten(column.get("field") or column.get("name") or column.get("key"))
        title = _flatten(column.get("displayName") or column.get("title") or column.get("label"))
        date_msg = _flatten(column.get("dateMsg") or "")
        if date_msg:
            title = f"{title} {date_msg}".strip()
        if key:
            name_map[key] = title or key
    return name_map


def _columns_order(columns: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    for column in columns or []:
        if not isinstance(column, dict):
            continue
        key = _flatten(column.get("field") or column.get("name") or column.get("key"))
        if key:
            ordered.append(key)
    return ordered


def _datalist_to_rows(datalist: list[dict[str, Any]], column_map: dict[str, str], column_order: list[str]) -> list[dict[str, str]]:
    if not datalist:
        return []
    first = datalist[0]
    extra_keys = [key for key in first if key not in column_order]
    header_order = column_order + extra_keys
    rows: list[dict[str, str]] = []
    for row in datalist:
        if not isinstance(row, dict):
            continue
        normalized: dict[str, str] = {}
        for key in header_order:
            if key not in row:
                continue
            normalized[column_map.get(key, key)] = _flatten(row[key])
        rows.append(normalized)
    return rows


def _parse_partial_results_table(partial_results: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in partial_results.strip().splitlines() if line.strip()]
    if not lines:
        return []

    def split_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.split("|") if cell.strip()]

    header = split_cells(lines[0])
    if not header:
        return []
    start_index = 1
    if start_index < len(lines) and re.match(r"^[\s\|\-]+$", lines[start_index]):
        start_index = 2

    rows: list[dict[str, str]] = []
    for line in lines[start_index:]:
        cells = split_cells(line)
        if len(cells) < len(header):
            cells.extend([""] * (len(header) - len(cells)))
        rows.append(dict(zip(header, cells[: len(header)])))
    return rows


def _news_type(value: Any) -> str:
    mapping = {"REPORT": "研报", "NEWS": "新闻", "ANNOUNCEMENT": "公告"}
    text = _flatten(value)
    return mapping.get(text, text or "资讯")


def _short_text(value: Any, limit: int = 120) -> str:
    text = _flatten(value).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
