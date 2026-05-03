from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import BASE_DIR


class MXProviderError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class MXQuerySpec:
    key: str
    label: str
    prompt: str


MX_SUMMARY_QUERIES = [
    MXQuerySpec("quote", "行情", "最新价 涨跌幅 成交额 换手率"),
    MXQuerySpec("fund_flow", "资金", "主力资金流向"),
    MXQuerySpec("valuation", "估值", "市盈率 市净率 总市值"),
    MXQuerySpec("financial_summary", "财务", "近三年营业收入 净利润 每股收益 ROE"),
    MXQuerySpec("company_profile", "公司", "公司简介 主营业务 董事长 总股本"),
]


class MXDataProvider:
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 20):
        self.api_key = api_key or _env_value("MX_APIKEY")
        self.timeout_seconds = timeout_seconds

    def summary(self, ts_code: str = "", name: str = "") -> dict[str, Any]:
        target = (name or ts_code).strip()
        if not target:
            raise MXProviderError("请输入股票名称或代码。", 400)
        if not self.api_key:
            raise MXProviderError("缺少 MX_APIKEY 环境变量，请先在服务端配置妙想金融数据 API Key。", 500)

        cards = []
        by_key: dict[str, Any] = {}
        for spec in MX_SUMMARY_QUERIES:
            card = self._card(spec, target)
            cards.append(card)
            by_key[spec.key] = card

        return {
            "stock": {"ts_code": ts_code, "name": name},
            "source": "mx-data",
            "cards": cards,
            **by_key,
        }

    def _card(self, spec: MXQuerySpec, target: str) -> dict[str, Any]:
        query_text = f"{target} {spec.prompt}"
        base = {"key": spec.key, "label": spec.label, "query_text": query_text}
        try:
            parsed = self.parse_response(self.query(query_text))
        except MXProviderError as exc:
            return {**base, "status": "error", "error": exc.message, "tables": [], "columns": [], "rows": []}

        tables = parsed["tables"]
        if not tables:
            return {**base, "status": "empty", "error": "MX 未返回有效表格数据。", "tables": [], "columns": [], "rows": []}

        first_table = tables[0]
        return {
            **base,
            "status": "ok",
            "title": first_table.get("title") or spec.label,
            "entities": parsed.get("entities", []),
            "question_id": parsed.get("question_id", ""),
            "tables": tables,
            "columns": first_table.get("columns", []),
            "rows": first_table.get("rows", []),
        }

    def query(self, tool_query: str) -> dict[str, Any]:
        if not self.api_key:
            raise MXProviderError("缺少 MX_APIKEY 环境变量，请先在服务端配置妙想金融数据 API Key。", 500)

        payload = json.dumps({"toolQuery": tool_query}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.BASE_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": self.api_key,
            },
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

    @staticmethod
    def parse_response(result: dict[str, Any]) -> dict[str, Any]:
        status = result.get("status")
        message = result.get("message", "")
        if status not in (0, "0", None):
            raise MXProviderError(f"MX 返回错误：{message or status}", 502)

        dto_list = _find_first_list(result, "dataTableDTOList")
        if not dto_list:
            return {"question_id": _find_first_value(result, "questionId"), "entities": [], "tables": []}

        tables: list[dict[str, Any]] = []
        for index, dto in enumerate(dto_list):
            if not isinstance(dto, dict):
                continue
            rows, columns = _table_to_rows(dto)
            if not rows:
                continue
            tables.append(
                {
                    "title": _flatten(dto.get("title") or dto.get("inputTitle") or dto.get("entityName") or f"表{index + 1}"),
                    "entity_name": _flatten(dto.get("entityName") or ""),
                    "code": _flatten(dto.get("code") or ""),
                    "columns": columns[:8],
                    "rows": [{key: row.get(key, "") for key in columns[:8]} for row in rows[:8]],
                    "total_rows": len(rows),
                }
            )

        return {
            "question_id": _flatten(_find_first_value(result, "questionId")),
            "entities": _entities(result),
            "tables": tables,
        }


def _table_to_rows(block: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    table = block.get("table") or block.get("rawTable") or {}
    if not isinstance(table, dict):
        return [], []

    name_map = block.get("nameMap") or {}
    if not isinstance(name_map, dict):
        name_map = {}

    headers = table.get("headName") or []
    if not isinstance(headers, list):
        headers = []

    keys = _ordered_table_keys(table, block.get("indicatorOrder") or [])
    columns = ["date"] + [_label_for_key(key, name_map) for key in keys]
    columns = [column for column in columns if column]

    rows: list[dict[str, str]] = []
    if headers:
        for row_index, header in enumerate(headers):
            row = {"date": _flatten(header)}
            for key in keys:
                label = _label_for_key(key, name_map)
                values = table.get(key, [])
                row[label] = _flatten(values[row_index] if isinstance(values, list) and row_index < len(values) else "")
            rows.append(row)
        return rows, columns

    max_length = max((len(value) for key, value in table.items() if key != "headName" and isinstance(value, list)), default=0)
    for row_index in range(max_length):
        row = {"date": str(row_index + 1)}
        for key in keys:
            label = _label_for_key(key, name_map)
            values = table.get(key, [])
            row[label] = _flatten(values[row_index] if isinstance(values, list) and row_index < len(values) else values)
        rows.append(row)
    return rows, columns


def _ordered_table_keys(table: dict[str, Any], indicator_order: list[Any]) -> list[str]:
    keys = [str(key) for key in table if key != "headName"]
    ordered = [str(key) for key in indicator_order if str(key) in keys]
    return ordered + [key for key in keys if key not in ordered]


def _label_for_key(key: str, name_map: dict[str, Any]) -> str:
    return _flatten(name_map.get(key) or name_map.get(str(key)) or key)


def _entities(result: dict[str, Any]) -> list[dict[str, str]]:
    tags = _find_first_list(result, "entityTagDTOList")
    entities = []
    for tag in tags or []:
        if not isinstance(tag, dict):
            continue
        entities.append(
            {
                "name": _flatten(tag.get("fullName") or tag.get("name") or ""),
                "code": _flatten(tag.get("secuCode") or tag.get("code") or ""),
                "type": _flatten(tag.get("entityTypeName") or ""),
                "market": _flatten(tag.get("marketChar") or ""),
            }
        )
    return entities[:6]


def _find_first_list(obj: Any, key: str) -> list[Any]:
    if isinstance(obj, dict):
        value = obj.get(key)
        if isinstance(value, list):
            return value
        for child in obj.values():
            found = _find_first_list(child, key)
            if found:
                return found
    elif isinstance(obj, list):
        for child in obj:
            found = _find_first_list(child, key)
            if found:
                return found
    return []


def _find_first_value(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for child in obj.values():
            found = _find_first_value(child, key)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for child in obj:
            found = _find_first_value(child, key)
            if found not in (None, ""):
                return found
    return ""


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value

    env_file = Path(BASE_DIR) / ".env"
    if not env_file.exists():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")
    return None
