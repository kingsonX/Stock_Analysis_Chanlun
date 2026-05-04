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

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 45,
    ):
        self.api_key = api_key or _env_value("CLAUDE_API_KEY")
        self.base_url = base_url or _env_value("CLAUDE_BASE_URL") or self.BASE_URL
        self.model = model or _env_value("CLAUDE_MODEL") or "Claude Sonnet 4.6"
        self.api_version = _env_value("CLAUDE_API_VERSION") or self.API_VERSION
        self.max_tokens = _safe_int(_env_value("CLAUDE_MAX_TOKENS"), 1800)
        self.timeout_seconds = timeout_seconds

    def explain(self, stock: dict[str, Any], analysis: dict[str, Any], profile_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise AIProviderError("缺少 CLAUDE_API_KEY 环境变量，暂时无法生成 Claude 研究解读。", 500)

        facts = _build_fact_packet(stock=stock, analysis=analysis, profile_payload=profile_payload)
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": _system_prompt(),
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "下面是当前股票的结构化事实，请严格基于这些事实输出 JSON，不要输出任何解释性前缀或 Markdown 代码块。\n"
                        f"返回格式要求：{_response_contract_text()}\n"
                        f"事实数据：{json.dumps(facts, ensure_ascii=False)}"
                    ),
                }
            ],
        }

        result = self._post_json(payload)
        content = _extract_json_content(result)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError("Claude 返回内容无法解析为结构化 JSON。", 502) from exc

        return {
            "status": "ok",
            "model": self.model,
            "facts": facts,
            "analysis": parsed,
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            _messages_url(self.base_url),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": self.api_version,
            },
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
            raise AIProviderError(_http_error_message(exc.code, body), 502) from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"Claude 网络访问失败：{exc.reason}", 502) from exc
        except TimeoutError as exc:
            raise AIProviderError("Claude 请求超时。", 504) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIProviderError("Claude 返回内容不是有效 JSON。", 502) from exc


OpenAIProfileExplainer = ClaudeProfileExplainer


def _http_error_message(status_code: int, body: str) -> str:
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}
    error = payload.get("error") or {}
    message = _flatten(error.get("message") or body or f"HTTP {status_code}")
    if status_code == 401:
        return f"Claude 鉴权失败：{message}"
    return f"Claude 请求失败：{message}"


def _extract_json_content(result: dict[str, Any]) -> str:
    texts: list[str] = []
    content = result.get("content") or []
    for item in content:
        if item.get("type") == "text":
            texts.append(item.get("text") or "")

    merged = _strip_json_fence("".join(texts).strip())
    if merged:
        return merged
    raise AIProviderError("Claude 没有返回可用文本。", 502)


def _system_prompt() -> str:
    return (
        "你是A股研究助理。请严格基于提供的事实，分别用缠中说禅、炒股养家、章建平三个视角，"
        "写出克制、可执行、像研究员写给交易员看的判断。"
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


def _messages_url(base_url: str) -> str:
    cleaned = (base_url or ClaudeProfileExplainer.BASE_URL).rstrip("/")
    if cleaned.endswith("/messages"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/messages"
    return f"{cleaned}/v1/messages"


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
