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
    stance, stance_label = _stance_label(total_score, structure, risk)

    conclusion = _conclusion_text(structure, emotion, capacity, risk, analysis)
    return {
        "stance": stance,
        "stance_label": stance_label,
        "headline": _headline_text(structure, emotion, capacity, risk),
        "conclusion": conclusion,
        "decision": _overall_decision(structure, emotion, capacity, risk),
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
    risk_cards = analysis.get("risk_cards") or []
    signal = _latest_signal(signals)
    divergence = divergences[-1] if divergences else None
    risk_card = _latest_risk_card(risk_cards, signal)

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
        tone = "positive"
    elif score <= -2:
        label = "结构偏空"
        tone = "caution"
    else:
        label = "结构观察"
        tone = "neutral"

    reason = trend.get("reason") or "当前结构仍在演化。"
    if divergence:
        reason = f"{reason} 最近背驰：{divergence.get('label') or '无'}。"

    if signal and signal.get("side") == "sell":
        verdict = "不宜买"
        action = "是否值得买：当前最后信号偏卖方，先把结构风险放在前面，不把反弹想成新买点。"
        conditions = [
            "先等卖点被后续结构修复，再重新评估。",
            "如果新的中枢继续上移、卖点失效，才说明空方压力减弱。",
        ]
        tone = "caution"
    elif signal and signal.get("side") == "buy" and signal.get("status") == "confirmed" and score >= 2:
        verdict = "可按纪律跟踪"
        action = f"是否值得买：结构上可以看多，但只能按确认买点处理，必须守住失效价 {_price_text(signal.get('invalidation_price'))}。"
        conditions = [
            "后续回踩不破失效价，买点结构才继续成立。",
            "若重新跌回中枢内部或出现更高级别卖点，优先降级为观察。",
        ]
        tone = "positive"
    elif signal and signal.get("side") == "buy":
        verdict = "候选观察"
        action = f"是否值得买：现在更像候选买点，不是确认买点，可以观察，暂不宜把它当成确定性上车位。"
        conditions = [
            "买点要从候选走到确认，至少要看到后续离开段继续成立。",
            f"若跌破失效价 {_price_text(signal.get('invalidation_price'))}，这笔买点假设就应取消。",
        ]
    elif score >= 2:
        verdict = "可继续跟踪"
        action = "是否值得买：结构偏强，但缺少清晰买点确认，更适合等回踩或下一次结构确认。"
        conditions = [
            "优先等新的买点出现，而不是在没有信号时追价。",
            "若中枢重心继续上移，结构才会从可看变成更强确认。",
        ]
    else:
        verdict = "先观察"
        action = "是否值得买：当前结构还不足以下明确买入结论，先把级别、位置和背驰大小看清。"
        conditions = [
            "至少等中枢方向和买卖点类别明确，再讨论是否参与。",
            "没有确认信号时，结构分析更适合做观察清单，不适合直接下结论。",
        ]

    basis = [
        f"级别：{query.get('level_label') or analysis.get('level') or '当前级别'}",
        f"走势：{trend.get('label') or '结构不足'}",
        f"位置：{trend.get('position_label') or '未知'}",
        f"信号：{signal_text}",
    ]
    if divergence:
        basis.append(f"最近背驰：{divergence.get('label') or '无'}")
    if risk_card and risk_card.get("invalidation_price") is not None:
        basis.append(f"失效价：{_price_text(risk_card.get('invalidation_price'))}")

    return {
        "label": label,
        "score": score,
        "title": "缠论结构",
        "summary": f"{query.get('level_label') or analysis.get('level') or '当前级别'} · {trend.get('label') or '结构不足'} · {signal_text}",
        "verdict": verdict,
        "action": action,
        "detail": f"理由：{reason}",
        "basis": basis,
        "conditions": conditions,
        "tone": tone,
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
        tone = "positive"
    elif score >= 1:
        label = "轮动可看"
        tone = "neutral"
    else:
        label = "情绪一般"
        tone = "caution"

    industry_name = _flatten(stock.get("industry") or "所属行业")
    summary = f"高涨幅个股 {market_total} 只，活跃成交股 {liquidity_total} 只，{industry_name} 活跃股 {industry_total} 只。"
    if hit_current_stock:
        summary = f"{summary} 当前标的出现在行业活跃扫描中。"

    first_news = recent_news[0] if recent_news else {}
    catalyst = _catalyst_judgement(first_news)
    detail = "理由：养家视角先看赚钱效应、主流强度和个股是否站在合力里。"
    if first_news:
        detail = f"{detail} 最近催化是{catalyst['level']}：{first_news.get('title', '')}。"

    if score >= 3 and hit_current_stock:
        verdict = "可以看，但别追高"
        action = "是否值得买：情绪面是加分项，这票可以进入观察池；只有主流继续扩散、板块反馈还强，才值得跟随。"
        conditions = [
            "次日或后续若高标、活跃股继续给正反馈，说明赚钱效应还在。",
            "若行业活跃扫描里这票掉队，或者市场高标开始补跌，就不该只凭情绪硬做。",
        ]
        tone = "positive"
    elif score >= 1:
        verdict = "可看不抢"
        action = "是否值得买：有轮动热度，但还没强到可以无条件跟，适合先看板块延续，不适合因为一条公告就追。"
        conditions = [
            "最好等行业活跃度继续抬升，再把它从观察名单升级为交易名单。",
            "如果只是公司级公告催化，而不是板块级催化，持续性要打折看。",
        ]
    else:
        verdict = "不靠情绪买"
        action = "是否值得买：单看情绪和主流维度还不够，赚钱效应一般时，不值得只凭热度上车。"
        conditions = [
            "先等高涨幅个股和活跃成交股数量明显回升。",
            "先等板块合力形成，再谈个股是否跟随。",
        ]

    basis = [
        f"高涨幅个股：{market_total} 只",
        f"活跃成交股：{liquidity_total} 只",
        f"{industry_name}活跃股：{industry_total} 只",
        f"当前标的{'命中' if hit_current_stock else '未命中'}行业活跃扫描",
    ]
    if first_news:
        basis.append(f"催化级别：{catalyst['level']}")

    return {
        "label": label,
        "score": score,
        "title": "养家视角",
        "summary": summary,
        "verdict": verdict,
        "action": action,
        "detail": detail,
        "basis": basis,
        "conditions": conditions,
        "tone": tone,
    }


def _capacity_summary(mx_summary: dict[str, Any]) -> dict[str, Any]:
    if mx_summary.get("status") != "ok":
        return {
            "label": "容量未知",
            "score": 0,
            "title": "章盟主视角",
            "summary": mx_summary.get("message") or "妙想行情数据暂不可用。",
            "verdict": "信息不足",
            "action": "是否值得买：这一维看不清时，不适合把仓位压在想象上。",
            "detail": "理由：章盟主视角先看成交承接、换手、市值容量和主力净额，没有这些数据就不下结论。",
            "basis": [],
            "conditions": ["等容量和资金数据恢复后，再评估是否适合参与。"],
            "tone": "neutral",
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
        tone = "positive"
    elif amount >= 1_000_000_000 or market_cap >= 10_000_000_000:
        score += 1
        label = "容量中等"
        tone = "neutral"
    else:
        label = "容量偏小"
        score -= 1 if amount > 0 or market_cap > 0 else 0
        tone = "caution"

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
    detail = f"理由：资金侧主力净额 {fund_flow_text or '-'}，章盟主视角看的是能不能承接、能不能进出，而不是图形漂不漂亮。"
    if score >= 3:
        verdict = "容量支持跟踪"
        action = "是否值得买：容量和承接都过关，若结构继续确认，值得纳入交易名单；但仍要看主力净额能否延续。"
        conditions = [
            "主力净流入继续为正，说明承接还在。",
            "若换手突然失衡、成交缩得太快，大资金视角就会降级。",
        ]
        tone = "positive"
    elif score >= 1:
        verdict = "容量够看，别冲动重仓"
        action = "是否值得买：可以看，但更适合结合结构分批观察，不适合只凭容量去赌。"
        conditions = [
            "先等结构确认和资金延续同时出现，再考虑提高级别。",
            "若主力净额转弱，说明容量只是表面，承接未必一致。",
        ]
    else:
        verdict = "容量不支持强做"
        action = "是否值得买：从章盟主的承接视角看，不值得为了题材想象去硬做。"
        conditions = [
            "至少要看到成交额和流动性改善，再谈是否进入大资金视野。",
            "流动性不足时，退出难度往往比买入理由更重要。",
        ]
        tone = "caution"
    basis = [
        f"成交额：{amount_text or '-'}",
        f"换手率：{turnover_text or '-'}",
        f"总市值：{market_cap_text or '-'}",
        f"主力净额：{fund_flow_text or '-'}",
    ]
    return {
        "label": label,
        "score": score,
        "title": "章盟主视角",
        "summary": summary,
        "verdict": verdict,
        "action": action,
        "detail": detail,
        "basis": basis,
        "conditions": conditions,
        "tone": tone,
    }


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

    if penalty == 0:
        verdict = "可按纪律执行"
        action = "是否值得买：风控上没有明显硬伤，但前提仍是结构和情绪能继续配合。"
        conditions = [
            "继续盯住失效价和公告节奏，别因为眼下没风险词就放松纪律。",
        ]
        tone = "positive"
    elif penalty <= 2:
        verdict = "带止损观察"
        action = "是否值得买：可以观察，但必须把失效价和公告风险放在买入理由前面。"
        conditions = [
            "一旦跌破失效价，或风险词继续发酵，就先取消结构假设。",
        ]
        tone = "neutral"
    else:
        verdict = "先回避风险"
        action = "是否值得买：当前风险边界不舒服，先别让结构好看掩盖公告和监管压力。"
        conditions = [
            "等风险词落地、结构重新修复后，再评估是否回到观察名单。",
        ]
        tone = "caution"

    basis = []
    if hits:
        basis.append(f"风险词：{hits[0]}")
    if invalidation is not None:
        basis.append(f"失效价：{_price_text(invalidation)}")
    if signal:
        basis.append(f"信号状态：{_signal_short_label(signal)} {signal.get('status_label') or ''}".strip())

    detail = "理由：章盟主视角会把锁定、监管、减持和流动性一起看，风控永远比故事更先兑现。"
    return {
        "label": label,
        "penalty": penalty,
        "title": "风控边界",
        "summary": summary,
        "verdict": verdict,
        "action": action,
        "detail": detail,
        "basis": basis,
        "conditions": conditions,
        "tone": tone,
    }


def _stance_label(total_score: int, structure: dict[str, Any], risk: dict[str, Any]) -> tuple[str, str]:
    if risk.get("penalty", 0) >= 3 or risk.get("tone") == "caution":
        return "caution", "风险优先"
    if structure.get("verdict") == "候选观察":
        return "neutral", "候选观察"
    if structure.get("score", 0) <= 0 and total_score > 0:
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
        return "综合结论：可以列入交易观察，但前提是结构买点继续确认、主流热度不掉、承接资金不转弱；否则仍按候选处理。"
    if signal and signal.get("side") == "buy":
        return "综合结论：结构有点，但还不到“看见买点就能下手”的程度，更像候选观察，不宜把技术点直接等同于环境确认。"
    if signal and signal.get("side") == "sell":
        return "综合结论：最后信号偏卖方，先看风险而不是想象，除非结构、情绪和资金三者一起修复，否则不把反抽当买点。"
    if risk["penalty"] >= 2:
        return "综合结论：现在先把公告和风险边界看清，再谈参与；风险没落地之前，漂亮结构也只能降级看。"
    return "综合结论：暂时没有特别强的共振信号，先等结构、主流和容量三条线至少有两条一起增强，再决定是否升级为可买观察。"


def _overall_decision(structure: dict[str, Any], emotion: dict[str, Any], capacity: dict[str, Any], risk: dict[str, Any]) -> str:
    if structure.get("tone") == "caution" or risk.get("tone") == "caution":
        return "是否值得买：先控制风险，不抢。"
    if structure.get("verdict") == "可按纪律跟踪" and emotion.get("score", 0) >= 1 and capacity.get("score", 0) >= 1:
        return "是否值得买：可跟踪，但只按确认条件和失效价执行。"
    if structure.get("verdict") == "候选观察":
        return "是否值得买：先观察，等候选变确认。"
    return "是否值得买：暂列观察名单，等共振更清楚。"


def _latest_signal(signals: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not signals:
        return None
    active = [item for item in signals if item.get("status") != "invalid"]
    return (active or signals)[-1]


def _latest_risk_card(risk_cards: list[dict[str, Any]], signal: dict[str, Any] | None) -> dict[str, Any] | None:
    if not risk_cards:
        return None
    if signal:
        signal_id = signal.get("id")
        for item in reversed(risk_cards):
            if item.get("signal_id") == signal_id:
                return item
    return risk_cards[-1]


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


def _catalyst_judgement(item: dict[str, Any]) -> dict[str, str]:
    text = f"{_flatten(item.get('title') or '')} {_flatten(item.get('summary') or '')}"
    strong_words = ("国务院", "工信部", "发改委", "财政部", "政策", "规划", "产业化", "补贴", "并购重组")
    medium_words = ("订单", "业绩", "中标", "合同", "投产", "合作", "回购")
    if any(word in text for word in strong_words):
        return {"level": "板块级/政策级催化"}
    if any(word in text for word in medium_words):
        return {"level": "公司经营催化"}
    if text:
        return {"level": "一般资讯催化"}
    return {"level": "暂无催化"}


def _price_text(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    text = f"{number:.3f}".rstrip("0").rstrip(".")
    return text or "0"


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
