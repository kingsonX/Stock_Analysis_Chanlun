from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .mx_provider import _env_value
from .trading_profile import _flatten


class AIProviderError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ClaudeProfileExplainer:
    BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"
    OPENAI_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
    OPENAI_MODEL = "doubao-seed-2-0-lite"
    OPENAI_THINKING = {"type": "disabled"}

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 120,
    ):
        ark_key = _env_value("ARK_API_KEY")
        ark_base_url = _env_value("ARK_BASE_URL")
        ark_endpoint_id = _env_value("ARK_ENDPOINT_ID")
        ark_model = _env_value("ARK_MODEL")
        kimi_key = _env_value("KIMI_API_KEY")
        kimi_base_url = _env_value("KIMI_BASE_URL")
        kimi_model = _env_value("KIMI_MODEL")
        claude_key = _env_value("CLAUDE_API_KEY")
        claude_base_url = _env_value("CLAUDE_BASE_URL")
        claude_model = _env_value("CLAUDE_MODEL")
        explicit_provider = _provider_from_model(model) or (_provider_kind(base_url, default="") if base_url else "")
        default_provider = explicit_provider or ("openai" if (ark_key or kimi_key) else "anthropic")

        self.api_key = api_key or ark_key or kimi_key or claude_key
        if base_url:
            self.base_url = base_url
        elif explicit_provider == "anthropic":
            self.base_url = claude_base_url or self.BASE_URL
        elif explicit_provider == "openai":
            self.base_url = ark_base_url or kimi_base_url or self.OPENAI_BASE_URL
        else:
            self.base_url = ark_base_url or kimi_base_url or claude_base_url or (self.OPENAI_BASE_URL if (ark_key or kimi_key) else self.BASE_URL)
        self.provider = _provider_kind(self.base_url, default=default_provider)
        self.openai_vendor = _openai_vendor(self.base_url, model or ark_model or kimi_model or "")
        self.provider_label = _provider_label(self.provider, self.openai_vendor)
        self.model = (
            model
            or (ark_endpoint_id or ark_model or kimi_model if self.provider == "openai" else claude_model)
            or (self.OPENAI_MODEL if self.provider == "openai" else "Claude Sonnet 4.6")
        )
        self.api_version = _env_value("CLAUDE_API_VERSION") or self.API_VERSION
        default_max_tokens = 900 if self.openai_vendor == "ark" else (1400 if self.provider == "openai" else 1800)
        self.max_tokens = _safe_int(
            _env_value("ARK_MAX_TOKENS") or _env_value("KIMI_MAX_TOKENS") or _env_value("CLAUDE_MAX_TOKENS"),
            default_max_tokens,
        )
        self.timeout_seconds = timeout_seconds

    def explain(self, stock: dict[str, Any], analysis: dict[str, Any], profile_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            missing_env = "ARK_API_KEY" if self.provider == "openai" else "CLAUDE_API_KEY"
            raise AIProviderError(f"缺少 {missing_env} 环境变量，暂时无法生成 {self.provider_label} 研究解读。", 500)

        facts = _build_fact_packet(stock=stock, analysis=analysis, profile_payload=profile_payload)
        payload = self._build_payload(facts)

        result = self._post_json(payload)
        content = self._extract_content(result)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"{self.provider_label} 返回内容无法解析为结构化 JSON。", 502) from exc

        return {
            "status": "ok",
            "model": self.model,
            "provider": self.provider_label,
            "facts": facts,
            "analysis": parsed,
        }

    def explain_review(self, review_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            missing_env = "ARK_API_KEY" if self.provider == "openai" else "CLAUDE_API_KEY"
            raise AIProviderError(f"缺少 {missing_env} 环境变量，暂时无法生成 {self.provider_label} 复盘结论。", 500)

        facts = _build_review_fact_packet(review_payload)
        payload = self._build_review_payload(facts)
        result = self._post_json(payload)
        content = self._extract_content(result)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"{self.provider_label} 返回的复盘内容无法解析为结构化 JSON。", 502) from exc

        return {
            "status": "ok",
            "model": self.model,
            "provider": self.provider_label,
            "facts": facts,
            "analysis": parsed,
        }

    def _build_payload(self, facts: dict[str, Any]) -> dict[str, Any]:
        user_prompt = (
            "下面是当前股票的结构化事实，请严格基于这些事实输出 JSON，不要输出任何解释性前缀或 Markdown 代码块。\n"
            "输出务必简洁：summary、buy_judgement、reason 控制在两句话内；basis、conditions、risks、watch_points 各最多 3 条，单条尽量不超过 24 个字。\n"
            f"返回格式要求：{_response_contract_text()}\n"
            f"事实数据：{json.dumps(facts, ensure_ascii=False)}"
        )
        if self.provider == "openai":
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": 0.6,
                "messages": [
                    {"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if self.openai_vendor in {"moonshot", "ark"}:
                payload["thinking"] = self.OPENAI_THINKING
            return payload

        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": _system_prompt(),
            "messages": [{"role": "user", "content": user_prompt}],
        }

    def _build_review_payload(self, facts: dict[str, Any]) -> dict[str, Any]:
        user_prompt = (
            "下面是智能复盘页面的结构化事实，请严格基于这些事实，"
            "从炒股养家公开心法的角度完成盘后复盘。"
            "你必须覆盖四个部分：指数复盘、情绪周期、盘面复盘、消息复盘。"
            "情绪周期必须参考事实里的 emotion_cycle，不要擅自切换到没有证据的阶段。"
            "同时更新关注板块和关注股票，且只能使用事实里已经给出的候选。"
            "输出务必是合法 JSON，不要加 Markdown 代码块或额外说明。\n"
            "一句话复盘、阶段判断、各分块 summary 保持短句；列表每项尽量不超过 24 个字。\n"
            f"返回格式要求：{_review_response_contract_text()}\n"
            f"事实数据：{json.dumps(facts, ensure_ascii=False)}"
        )
        system_prompt = _review_system_prompt()
        if self.provider == "openai":
            payload = {
                "model": self.model,
                "max_tokens": max(self.max_tokens, 1600),
                "temperature": 0.6,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if self.openai_vendor in {"moonshot", "ark"}:
                payload["thinking"] = self.OPENAI_THINKING
            return payload

        return {
            "model": self.model,
            "max_tokens": max(self.max_tokens, 1800),
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = _chat_completions_url(self.base_url) if self.provider == "openai" else _messages_url(self.base_url)
        headers = {"Content-Type": "application/json"}
        if self.provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = self.api_version

        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""
            raise AIProviderError(_http_error_message(self.provider_label, exc.code, body), 502) from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"{self.provider_label} 网络访问失败：{exc.reason}", 502) from exc
        except TimeoutError as exc:
            raise AIProviderError(f"{self.provider_label} 请求超时。", 504) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"{self.provider_label} 返回内容不是有效 JSON。", 502) from exc

    def _extract_content(self, result: dict[str, Any]) -> str:
        if self.provider == "openai":
            return _extract_openai_json_content(result, self.provider_label)
        return _extract_json_content(result, self.provider_label)


OpenAIProfileExplainer = ClaudeProfileExplainer
KimiProfileExplainer = ClaudeProfileExplainer


def _http_error_message(provider_label: str, status_code: int, body: str) -> str:
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}
    error = payload.get("error") or {}
    message = _flatten(error.get("message") or body or f"HTTP {status_code}")
    if status_code == 401:
        return f"{provider_label} 鉴权失败：{message}"
    if provider_label == "火山方舟" and status_code == 404 and (
        "does not exist or you do not have access" in message.lower()
        or "accessing the model via model id is not allowed" in message.lower()
    ):
        return (
            f"{provider_label} 请求失败：{message}。"
            "请确认 `model` 使用的是已开通的模型或推理接入点 ID（常见为 `ep-` 开头），而不是无权限的模型名。"
        )
    return f"{provider_label} 请求失败：{message}"


def _extract_json_content(result: dict[str, Any], provider_label: str = "Claude") -> str:
    texts: list[str] = []
    content = result.get("content") or []
    for item in content:
        if item.get("type") == "text":
            texts.append(item.get("text") or "")

    merged = _strip_json_fence("".join(texts).strip())
    if merged:
        return merged
    raise AIProviderError(f"{provider_label} 没有返回可用文本。", 502)


def _extract_openai_json_content(result: dict[str, Any], provider_label: str = "OpenAI兼容模型") -> str:
    choices = result.get("choices") or []
    if not choices:
        raise AIProviderError(f"{provider_label} 没有返回可用结果。", 502)
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(_flatten(item.get("text") if isinstance(item, dict) else item) for item in content)
    merged = _strip_json_fence(_flatten(content).strip())
    if merged:
        return merged
    raise AIProviderError(f"{provider_label} 没有返回可用文本。", 502)


def _system_prompt() -> str:
    return (
        "你是A股研究助理。请严格基于提供的事实，分别用缠中说禅、炒股养家、章建平三个视角，"
        "写出克制、可执行、像研究员写给交易员看的判断。"
        "输出要短，适合直接展示在交易工作台卡片中。"
        "不要编造龙虎榜、盘口、机构持仓、内幕消息或额外公告。"
        "不要承诺收益，不要输出确定性荐股措辞。"
        "买入表达只能使用可跟踪、候选观察、暂不参与、风险回避这类克制口径。"
        "返回内容必须是合法 JSON，键名必须完全匹配要求，不要输出 Markdown 代码块。"
    )


def _response_contract_text() -> str:
    return json.dumps(
        {
            "summary": "string",
            "overall_verdict": "重点观察|候选观察|暂不参与|风险回避",
            "buy_judgement": "string",
            "confidence": "高|中|低",
            "chan_view": {
                "verdict": "string",
                "buyable": "string",
                "reason": "string",
                "basis": ["string"],
                "conditions": ["string"],
            },
            "yangjia_view": {
                "verdict": "string",
                "buyable": "string",
                "reason": "string",
                "basis": ["string"],
                "conditions": ["string"],
            },
            "zhang_view": {
                "verdict": "string",
                "buyable": "string",
                "reason": "string",
                "basis": ["string"],
                "conditions": ["string"],
            },
            "risks": ["string"],
            "watch_points": ["string"],
        },
        ensure_ascii=False,
    )


def _review_system_prompt() -> str:
    return (
        "你是A股短线复盘助理，站在炒股养家公开心法的表达框架里做盘后总结。"
        "先判断市场阶段，再判断赚钱效应和亏钱效应，再看主流热点与龙头辨识度，最后给观察重点和风险边界。"
        "情绪周期阶段以输入事实 emotion_cycle 为锚，允许补充解释，不允许脱离事实改判。"
        "不要编造指数、龙虎榜、游资、政策、资金流、连板或新闻。"
        "不能输出荐股、梭哈、必涨这类措辞。"
        "关注板块和关注股票只能从输入事实已有候选里挑选并排序。"
        "返回内容必须是合法 JSON。"
    )


def _review_response_contract_text() -> str:
    return json.dumps(
        {
            "summary": "string",
            "market_stage": "强势推进|主流试错|分歧整理|退潮防守",
            "index_review": {
                "summary": "string",
                "signals": ["string"],
            },
            "emotion_cycle": {
                "phase": "低位分歧|分歧转强（弱转强）|加速（大阳线）|一致（高潮）|高位分歧|分歧转弱（强转弱）|分歧加速|冰点（一致）",
                "summary": "string",
                "signals": ["string"],
            },
            "tape_review": {
                "summary": "string",
                "hot_themes": ["string"],
                "fund_flow": ["string"],
                "limit_watch": ["string"],
            },
            "news_review": {
                "summary": "string",
                "catalysts": ["string"],
                "ladder_focus": ["string"],
            },
            "watch_points": ["string"],
            "risk_points": ["string"],
            "focus_boards": [
                {"name": "string", "reason": "string", "action": "string"}
            ],
            "focus_stocks": [
                {"ts_code": "string", "name": "string", "reason": "string", "action": "string"}
            ],
        },
        ensure_ascii=False,
    )


def _messages_url(base_url: str) -> str:
    cleaned = (base_url or ClaudeProfileExplainer.BASE_URL).rstrip("/")
    if cleaned.endswith("/messages"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/messages"
    return f"{cleaned}/v1/messages"


def _chat_completions_url(base_url: str) -> str:
    cleaned = (base_url or ClaudeProfileExplainer.OPENAI_BASE_URL).rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1") or cleaned.endswith("/api/v3") or cleaned.endswith("/api/coding/v3"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def _provider_kind(base_url: str | None, default: str = "anthropic") -> str:
    cleaned = (base_url or "").lower()
    if "moonshot" in cleaned or "openai" in cleaned or "chat/completions" in cleaned or "volces" in cleaned or "ark." in cleaned or "/api/v3" in cleaned:
        return "openai"
    if "anthropic" in cleaned or cleaned.endswith("/messages"):
        return "anthropic"
    return default


def _provider_from_model(model: str | None) -> str:
    text = _flatten(model or "").lower()
    if (
        "kimi" in text
        or text.startswith("ark-")
        or "ark-code" in text
        or text.startswith("doubao-")
        or text.startswith("deepseek-")
        or text.startswith("glm-")
    ):
        return "openai"
    if "claude" in text:
        return "anthropic"
    return ""


def _openai_vendor(base_url: str | None, model: str | None) -> str:
    cleaned_base = (base_url or "").lower()
    cleaned_model = _flatten(model or "").lower()
    if "moonshot" in cleaned_base or "kimi" in cleaned_model:
        return "moonshot"
    if "volces" in cleaned_base or "ark." in cleaned_base or cleaned_model.startswith("ark-") or "ark-code" in cleaned_model:
        return "ark"
    return "generic"


def _provider_label(provider: str, openai_vendor: str) -> str:
    if provider != "openai":
        return "Claude"
    if openai_vendor == "moonshot":
        return "Kimi"
    if openai_vendor == "ark":
        return "火山方舟"
    return "OpenAI兼容模型"


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.lstrip("`")
        if "\n" in stripped:
            stripped = stripped.split("\n", 1)[1]
        stripped = stripped.rsplit("```", 1)[0].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return stripped[start : end + 1]
    return stripped


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _build_fact_packet(stock: dict[str, Any], analysis: dict[str, Any], profile_payload: dict[str, Any]) -> dict[str, Any]:
    profile = profile_payload.get("profile") or {}
    structure = profile.get("structure") or {}
    emotion = profile.get("emotion") or {}
    capacity = profile.get("capacity") or {}
    risk = profile.get("risk") or {}

    latest_signal = (analysis.get("signals") or [])[-1] if analysis.get("signals") else {}
    latest_divergence = (analysis.get("divergences") or [])[-1] if analysis.get("divergences") else {}
    news_items = (profile_payload.get("news") or {}).get("items") or []
    market_cards = (profile_payload.get("market_scan") or {}).get("cards") or []

    return {
        "stock": {
            "name": stock.get("name", ""),
            "symbol": stock.get("symbol", ""),
            "ts_code": stock.get("ts_code", ""),
            "industry": stock.get("industry", ""),
        },
        "overall": {
            "stance": profile.get("stance_label", ""),
            "headline": profile.get("headline", ""),
            "decision": profile.get("decision", ""),
            "conclusion": profile.get("conclusion", ""),
            "tags": profile.get("tags", []),
        },
        "structure": {
            "summary": structure.get("summary", ""),
            "verdict": structure.get("verdict", ""),
            "action": structure.get("action", ""),
            "detail": structure.get("detail", ""),
            "basis": structure.get("basis", []),
            "conditions": structure.get("conditions", []),
        },
        "yangjia": {
            "summary": emotion.get("summary", ""),
            "verdict": emotion.get("verdict", ""),
            "action": emotion.get("action", ""),
            "detail": emotion.get("detail", ""),
            "basis": emotion.get("basis", []),
            "conditions": emotion.get("conditions", []),
        },
        "zhang": {
            "summary": capacity.get("summary", ""),
            "verdict": capacity.get("verdict", ""),
            "action": capacity.get("action", ""),
            "detail": capacity.get("detail", ""),
            "basis": capacity.get("basis", []),
            "conditions": capacity.get("conditions", []),
        },
        "risk": {
            "summary": risk.get("summary", ""),
            "verdict": risk.get("verdict", ""),
            "action": risk.get("action", ""),
            "detail": risk.get("detail", ""),
            "basis": risk.get("basis", []),
            "conditions": risk.get("conditions", []),
        },
        "latest_structure_signal": {
            "label": _flatten(latest_signal.get("label") or latest_signal.get("type") or ""),
            "side": _flatten(latest_signal.get("side") or ""),
            "status": _flatten(latest_signal.get("status_label") or latest_signal.get("status") or ""),
            "price": _flatten(latest_signal.get("price") or ""),
            "invalidation_price": _flatten(latest_signal.get("invalidation_price") or ""),
        },
        "latest_divergence": {
            "label": _flatten(latest_divergence.get("label") or ""),
            "date": _flatten(latest_divergence.get("date") or ""),
            "price": _flatten(latest_divergence.get("price") or ""),
        },
        "market_scan": [
            {
                "label": item.get("label", ""),
                "status": item.get("status", ""),
                "description": item.get("description", ""),
                "hit_current_stock": bool(item.get("hit_current_stock")),
                "total": item.get("total", 0),
            }
            for item in market_cards[:4]
        ],
        "news": [
            {
                "title": item.get("title", ""),
                "type": item.get("type", ""),
                "date": item.get("date", ""),
                "summary": item.get("summary", ""),
            }
            for item in news_items[:4]
        ],
    }


def _build_review_fact_packet(review_payload: dict[str, Any]) -> dict[str, Any]:
    summary = review_payload.get("summary") or {}
    notes = review_payload.get("notes") or {}
    indices = (review_payload.get("market_indices") or {}).get("items") or []
    dragon = review_payload.get("dragon_tiger") or []
    hot_money = review_payload.get("hot_money_trades") or []
    limit_lists = review_payload.get("limit_lists") or {}
    ladder = review_payload.get("ladder") or []
    focus_boards = review_payload.get("focus_boards") or []
    focus_stocks = review_payload.get("focus_stocks") or []
    emotion_cycle = review_payload.get("emotion_cycle") or {}

    return {
        "trade_date": review_payload.get("trade_date", ""),
        "summary": {
            "dragon_count": summary.get("dragon_count", 0),
            "hot_money_count": summary.get("hot_money_count", 0),
            "up_limit_count": summary.get("up_limit_count", 0),
            "down_limit_count": summary.get("down_limit_count", 0),
            "burst_count": summary.get("burst_count", 0),
            "highest_board": summary.get("highest_board", 0),
            "focus_board_count": summary.get("focus_board_count", 0),
            "focus_stock_count": summary.get("focus_stock_count", 0),
        },
        "market_indices": [
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "close": item.get("close", ""),
                "pct_chg": item.get("pct_chg", ""),
                "amount": item.get("amount", ""),
                "pe": item.get("pe", ""),
                "pb": item.get("pb", ""),
                "turnover_rate": item.get("turnover_rate", ""),
            }
            for item in indices[:3]
        ],
        "dragon_tiger": [
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "pct_change": item.get("pct_change", ""),
                "net_amount": item.get("net_amount", ""),
                "reason": item.get("reason", ""),
            }
            for item in dragon[:8]
        ],
        "hot_money_trades": [
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "hot_money_label": item.get("hot_money_label", ""),
                "net_amount": item.get("net_amount", ""),
                "tag": item.get("tag", ""),
            }
            for item in hot_money[:8]
        ],
        "limit_stats": {
            "up_preview": [
                {"ts_code": item.get("ts_code", ""), "name": item.get("name", ""), "limit_times": item.get("limit_times", ""), "strth": item.get("strth", "")}
                for item in (limit_lists.get("up") or [])[:6]
            ],
            "burst_preview": [
                {"ts_code": item.get("ts_code", ""), "name": item.get("name", ""), "open_times": item.get("open_times", ""), "fd_amount": item.get("fd_amount", "")}
                for item in (limit_lists.get("burst") or [])[:6]
            ],
            "down_preview": [
                {"ts_code": item.get("ts_code", ""), "name": item.get("name", ""), "pct_chg": item.get("pct_chg", "")}
                for item in (limit_lists.get("down") or [])[:6]
            ],
        },
        "emotion_cycle": {
            "phase_key": emotion_cycle.get("phase_key", ""),
            "phase": emotion_cycle.get("phase", ""),
            "stage": emotion_cycle.get("stage", ""),
            "summary": emotion_cycle.get("summary", ""),
            "basis": emotion_cycle.get("basis", []),
            "action": emotion_cycle.get("action", ""),
            "risk": emotion_cycle.get("risk", ""),
            "metrics": emotion_cycle.get("metrics", {}),
        },
        "ladder": [
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "continue_num": item.get("continue_num", ""),
                "concept": item.get("concept", ""),
                "pct_chg": item.get("pct_chg", ""),
            }
            for item in ladder[:8]
        ],
        "rule_notes": notes,
        "focus_board_candidates": [
            {
                "name": item.get("name", ""),
                "rank": item.get("rank", ""),
                "limit_count": item.get("limit_count", ""),
                "pct_chg": item.get("pct_chg", ""),
                "watch_reason": item.get("watch_reason", ""),
            }
            for item in focus_boards[:8]
        ],
        "focus_stock_candidates": [
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "score": item.get("score", ""),
                "tags": item.get("tags", []),
                "reason": item.get("reason", ""),
                "verdict": item.get("verdict", ""),
            }
            for item in focus_stocks[:10]
        ],
    }
