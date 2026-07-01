from __future__ import annotations

import json
import math
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta
from typing import Any

from .ai_profile import AIProviderError, _chat_completions_url, _extract_openai_json_content, _http_error_message
from .credential_service import CredentialService, CredentialServiceError
from .data_provider import DataProviderError, TushareClient
from .mx_provider import MXDataProvider, MXProviderError
from .mysql_store import mysql_connection
from .system_config_store import mysql_dsn_from_env


class ThemeResearchError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EastMoneyMiaoxiangClient:
    SEARCH_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search"

    def __init__(self, api_key: str, timeout_seconds: int = 30):
        self.api_key = str(api_key or "").strip()
        self.timeout_seconds = max(5, int(timeout_seconds))
        self.data_provider = MXDataProvider(api_key=self.api_key, timeout_seconds=self.timeout_seconds)

    def search_theme_events(self, theme_name: str, days: int = 30) -> dict[str, Any]:
        query = f"{theme_name} 最近{days}天 产业事件 政策催化 市场热点 涨价 国产替代 供需变化 AI算力"
        items = self._search_items(query)
        return {
            "status": "ok",
            "query": query,
            "items": items[:12],
            "count": len(items),
        }

    def search_news(self, query: str, days: int = 30) -> dict[str, Any]:
        search_query = f"{query} 最近{days}天 新闻 研报"
        items = [item for item in self._search_items(search_query) if item.get("info_type") != "ANNOUNCEMENT"]
        return {
            "status": "ok",
            "query": search_query,
            "items": items[:18],
            "count": len(items),
        }

    def search_announcements(self, query: str, days: int = 90) -> dict[str, Any]:
        search_query = f"{query} 最近{days}天 公告 风险提示 互动易"
        items = [item for item in self._search_items(search_query) if item.get("info_type") == "ANNOUNCEMENT"]
        if not items:
            items = [
                item
                for item in self._search_items(search_query)
                if "公告" in str(item.get("title") or "") or "公告" in str(item.get("summary") or "")
            ]
        for item in items:
            item["evidence_level"] = "S"
        return {
            "status": "ok",
            "query": search_query,
            "items": items[:12],
            "count": len(items),
        }

    def search_sentiment(self, theme_name: str, days: int = 7) -> dict[str, Any]:
        query = f"{theme_name} 最近{days}天 舆情 热度 讨论度 情绪"
        items = self._search_items(query)
        for item in items:
            item["evidence_level"] = "C"
        return {
            "status": "ok",
            "query": query,
            "items": items[:10],
            "count": len(items),
        }

    def search_related_stocks(self, theme_name: str) -> dict[str, Any]:
        query = f"{theme_name} A股相关公司 主营业务 最新价 涨跌幅 总市值"
        try:
            parsed = MXDataProvider.parse_response(self.data_provider.query(query))
        except MXProviderError:
            raise
        except Exception as exc:
            raise MXProviderError(f"妙想相关股票查询失败：{exc}", 502) from exc

        entities = []
        seen: set[str] = set()
        for entity in parsed.get("entities", []):
            code = str(entity.get("code") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            entities.append(
                {
                    "ts_code": _normalize_ts_code(code, market=str(entity.get("market") or "")),
                    "name": str(entity.get("name") or "").strip(),
                    "source": "东方财富妙想",
                    "publish_time": "",
                    "summary": "妙想结构化相关股票命中。",
                    "url": "",
                    "evidence_level": "A",
                }
            )
        return {
            "status": "ok",
            "query": query,
            "items": entities[:12],
            "tables": parsed.get("tables", []),
            "count": len(entities),
        }

    def _search_items(self, query: str) -> list[dict[str, Any]]:
        payload = json.dumps({"query": query}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.SEARCH_URL,
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
            raise MXProviderError(f"妙想资讯请求失败：HTTP {exc.code}", 502) from exc
        except urllib.error.URLError as exc:
            raise MXProviderError(f"妙想资讯网络访问失败：{exc.reason}", 502) from exc
        except TimeoutError as exc:
            raise MXProviderError("妙想资讯请求超时。", 504) from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MXProviderError("妙想资讯返回内容不是有效 JSON。", 502) from exc

        status = result.get("status")
        if status not in (0, "0", None):
            raise MXProviderError(f"妙想资讯返回错误：{result.get('message') or status}", 502)

        items = []
        rows = (((result.get("data") or {}).get("data") or {}).get("llmSearchResponse") or {}).get("data") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            info_type = str(row.get("informationType") or "").strip().upper()
            title = str(row.get("title") or "").strip()
            summary = str(row.get("content") or "").strip()
            publish_time = str(row.get("date") or "").strip()
            source = str(row.get("insName") or row.get("source") or "东方财富妙想").strip()
            items.append(
                {
                    "title": title,
                    "source": source,
                    "publish_time": publish_time,
                    "summary": summary,
                    "url": str(row.get("url") or row.get("sourceUrl") or row.get("link") or "").strip(),
                    "evidence_level": _mx_search_evidence_level(info_type),
                    "info_type": info_type,
                    "entity_name": str(row.get("entityFullName") or "").strip(),
                    "rating": str(row.get("rating") or "").strip(),
                }
            )
        return items


class ThemeResearchAgent:
    SYSTEM_PROMPT = (
        "你是一名 A股产业链研究员 + 科技行业分析师 + 短中线资金研究员。"
        "核心原则：先证伪，再证实；业绩是根，逻辑是魂。"
        "不要只讲概念，必须判断产业链真实位置、实锚关系、业绩兑现和 A股映射。"
        "你必须优先使用工具结果，不允许凭记忆编造公告、新闻、财务、客户、订单、供应链关系；"
        "不确定的信息必须标注“待核实”；C级舆情只能用于情绪判断。"
        "输出必须是合法 JSON，不要输出 Markdown 代码块。"
    )

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-pro",
        max_tokens: int = 5200,
        reasoning_effort: str = "high",
        timeout_seconds: int = 120,
    ):
        self.api_key = str(api_key or "").strip()
        self.base_url = str(base_url or "").strip() or "https://api.deepseek.com"
        self.model = str(model or "").strip() or "deepseek-v4-pro"
        self.max_tokens = max(1600, int(max_tokens))
        self.reasoning_effort = str(reasoning_effort or "high").strip() or "high"
        self.timeout_seconds = max(10, int(timeout_seconds))
        self.provider_label = "DeepSeek"

    def normalize_theme(self, theme_name: str, market: str, analysis_depth: str, time_horizon: str) -> dict[str, Any]:
        prompt = (
            "请把用户输入的 A 股题材名称标准化，只返回 JSON。"
            "返回字段：theme_name、normalized_name、keywords、stage_guess、current_drivers。"
            "keywords 至少 4 个，最多 8 个。"
            "如果英文缩写有常见中文全称，请补成中文标准名。"
            f"输入：{json.dumps({'theme_name': theme_name, 'market': market, 'analysis_depth': analysis_depth, 'time_horizon': time_horizon}, ensure_ascii=False)}"
        )
        return self._call_json(prompt, max_tokens=1200, repair_label="题材标准化")

    def plan_industry_tree(self, facts: dict[str, Any]) -> dict[str, Any]:
        prompt = self._build_industry_tree_prompt(facts)
        result = self._call_json(
            prompt,
            max_tokens=min(max(self.max_tokens, 2200), 3200),
            repair_label="题材 MECE 行业树",
            reasoning_effort="low",
            enable_thinking=False,
        )
        return _normalize_industry_tree(result, facts)

    def refine_industry_tree(
        self,
        facts: dict[str, Any],
        current_tree: dict[str, Any],
        quality_report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback_retry = _industry_tree_is_fallback(current_tree)
        retry_feedback = _industry_tree_quality_feedback(quality_report)
        if fallback_retry:
            retry_feedback = f"上一次结果仍停留在业务/股权/情绪映射兜底，不是真正的行业树。{retry_feedback}"
        prompt = self._build_industry_tree_prompt(
            facts,
            retry_feedback=retry_feedback,
            previous_tree=None if fallback_retry else current_tree,
        )
        result = self._call_json(
            prompt,
            max_tokens=min(max(self.max_tokens, 2600), 3600),
            repair_label="题材 MECE 行业树复核",
            reasoning_effort="low",
            enable_thinking=False,
        )
        return _normalize_industry_tree(result, facts)

    def _build_industry_tree_prompt(
        self,
        facts: dict[str, Any],
        retry_feedback: str = "",
        previous_tree: dict[str, Any] | None = None,
    ) -> str:
        prompt = (
            "请先对这个 A 股题材做 MECE 行业拆分，只返回 JSON。"
            "拆分原则："
            "1. 先从题材概念本身选择一个一致的一级拆分维度，优先考虑技术路线、终端场景、产业链层级、材料/设备/制造等高层维度；"
            "2. 不要被单一公司、单一器件或当前分数最高的细分绑架，要先把题材主干路线拆全；"
            "3. 一级节点必须互斥且尽量穷尽，控制在 2-6 个；如果个别分支暂时没有公司映射，也要保留并写“待核实”；"
            "4. 每个一级节点继续向下拆 1-3 层，直到形成可读的细分叶子；叶子节点允许没有公司；"
            "5. 不允许新增事实包里没有出现过的 A 股公司；"
            "6. 每家公司最多只能出现在一个最匹配的叶子节点里；"
            "7. summary 要简洁，dimension_reason 要说明为什么选这个拆分维度；"
            "8. 不确定的信息明确写“待核实”；"
            "9. 例如储能应先选一个一致维度：要么按技术路线拆成机械储能/电化学储能/热储能，要么按应用场景拆成户用/工商业/电网侧，不要把不同维度混在同一层。"
        )
        if retry_feedback:
            prompt += (
                "\n第一次返回的行业树存在这些缺口，请你按缺口重做，不是只改措辞："
                f"{retry_feedback}"
            )
        if previous_tree:
            prompt += f"\n上一次行业树：{json.dumps(_compact_industry_tree_for_prompt(previous_tree), ensure_ascii=False)}"
        prompt += (
            f"\n返回 JSON Schema：{json.dumps(_empty_industry_tree_schema(), ensure_ascii=False)}\n"
            f"事实包：{json.dumps(facts, ensure_ascii=False)}"
        )
        return prompt

    def generate_report(self, facts: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "下面是题材研究事实包，请严格基于事实生成完整研究报告 JSON。"
            "你必须：1. 先证伪，再证实；2. 明确区分业务锚点、股权锚点、情绪映射；"
            "3. 对无法确认的信息明确写“待核实”；4. scoring_table 优先使用输入里已经给出的分数；"
            "5. sources 只允许引用输入事实里的来源；6. 不能新增输入里没有出现的 A 股公司；"
            "7. industry_tree 必须优先复用输入里的 industry_tree_plan，并保持 MECE 拆分；"
            "8. 如果输入里的 industry_tree_plan 标记为需要重建，或仍是业务/股权/情绪兜底树，你必须基于事实包重新生成更细的 MECE 行业树，不能照抄兜底结构。"
            f"返回 JSON Schema：{json.dumps(_empty_report_schema(), ensure_ascii=False)}\n"
            f"事实包：{json.dumps(facts, ensure_ascii=False)}"
        )
        return self._call_json(
            prompt,
            max_tokens=max(self.max_tokens, 4200),
            repair_label="题材研究报告",
            reasoning_effort="low",
            enable_thinking=False,
        )

    def _call_json(
        self,
        user_prompt: str,
        max_tokens: int,
        repair_label: str,
        reasoning_effort: str | None = None,
        enable_thinking: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stream": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        if enable_thinking:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = str(reasoning_effort or self.reasoning_effort or "high").strip() or "high"
        result = self._post_json(payload)
        content = _extract_openai_json_content(result, self.provider_label)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            repaired = self._repair_json(content, repair_label=repair_label)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as exc:
                raise AIProviderError(f"{self.provider_label} 返回的 {repair_label} 仍然无法解析为 JSON。", 502) from exc

    def _repair_json(self, raw_content: str, repair_label: str) -> str:
        repair_prompt = (
            f"下面是一段本应是 JSON 的 {repair_label} 内容，但格式有问题。"
            "请只返回修复后的合法 JSON，不要补充解释。\n"
            f"{raw_content}"
        )
        payload = {
            "model": self.model,
            "max_tokens": 2200,
            "temperature": 0,
            "stream": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "你是 JSON 修复器，只返回合法 JSON。"},
                {"role": "user", "content": repair_prompt},
            ],
        }
        result = self._post_json(payload)
        return _extract_openai_json_content(result, self.provider_label)

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            _chat_completions_url(self.base_url),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
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
            raise AIProviderError(_http_error_message(self.provider_label, exc.code, body), 502) from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"{self.provider_label} 网络访问失败：{exc.reason}", 502) from exc
        except TimeoutError as exc:
            raise AIProviderError(f"{self.provider_label} 请求超时。", 504) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"{self.provider_label} 返回内容不是有效 JSON。", 502) from exc


class ThemeResearchStore:
    def __init__(self, dsn: str | None = None):
        self.dsn = str(dsn or mysql_dsn_from_env() or "").strip()
        self._schema_ready = False

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    def create_task(self, task_id: str, theme_name: str, market: str, analysis_depth: str, time_horizon: str) -> dict[str, Any]:
        self._ensure_enabled()
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                insert into theme_research_tasks (
                  task_id, theme_name, market, analysis_depth, time_horizon, status
                ) values (%s, %s, %s, %s, %s, %s)
                """,
                (task_id, theme_name, market, analysis_depth, time_horizon, "created"),
            )
        return self.get_task(task_id) or {}

    def update_task_status(self, task_id: str, status: str) -> None:
        self._ensure_enabled()
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                update theme_research_tasks
                set status = %s, updated_at = current_timestamp
                where task_id = %s
                """,
                (status, task_id),
            )

    def append_event(
        self,
        task_id: str,
        step_no: int,
        step_title: str,
        status: str,
        message: str = "",
        data_preview: Any = None,
        event_type: str = "step_update",
    ) -> dict[str, Any]:
        self._ensure_enabled()
        payload = json.dumps(data_preview, ensure_ascii=False) if data_preview not in (None, "") else ""
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                insert into theme_research_steps (
                  task_id, step_no, step_title, event_type, status, message, data_preview
                ) values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (task_id, step_no, step_title, event_type, status, message, payload),
            )
            row_id = cur.lastrowid
        return self.get_step(row_id) or {}

    def save_report(self, task_id: str, theme_name: str, report_json: dict[str, Any]) -> dict[str, Any]:
        self._ensure_enabled()
        report_text = json.dumps(report_json, ensure_ascii=False)
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                insert into theme_research_reports (task_id, theme_name, report_json)
                values (%s, %s, %s)
                on duplicate key update
                  theme_name = values(theme_name),
                  report_json = values(report_json),
                  updated_at = current_timestamp
                """,
                (task_id, theme_name, report_text),
            )
        return self.get_report(task_id) or {}

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select task_id, theme_name, market, analysis_depth, time_horizon, status, created_at, updated_at
                from theme_research_tasks
                where task_id = %s
                limit 1
                """,
                (task_id,),
            )
            row = cur.fetchone()
        return _serialize_db_row(row)

    def get_step(self, step_id: int) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select id, task_id, step_no, step_title, event_type, status, message, data_preview, created_at
                from theme_research_steps
                where id = %s
                limit 1
                """,
                (int(step_id),),
            )
            row = cur.fetchone()
        return _serialize_step_row(row)

    def list_steps(self, task_id: str, after_id: int = 0) -> list[dict[str, Any]]:
        self._ensure_enabled()
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select id, task_id, step_no, step_title, event_type, status, message, data_preview, created_at
                from theme_research_steps
                where task_id = %s and id > %s
                order by id asc
                """,
                (task_id, int(after_id)),
            )
            rows = cur.fetchall() or []
        return [_serialize_step_row(row) for row in rows if row]

    def get_report(self, task_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select task_id, theme_name, report_json, created_at, updated_at
                from theme_research_reports
                where task_id = %s
                limit 1
                """,
                (task_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        report_text = str(row.get("report_json") or "")
        try:
            payload = json.loads(report_text) if report_text else {}
        except json.JSONDecodeError:
            payload = {}
        return {
            "task_id": str(row.get("task_id") or ""),
            "theme_name": str(row.get("theme_name") or ""),
            "report": payload,
            "created_at": str(row.get("created_at") or ""),
            "updated_at": str(row.get("updated_at") or ""),
        }

    def list_reports(self, limit: int = 12, page: int = 1, page_size: int | None = None) -> dict[str, Any]:
        self._ensure_enabled()
        safe_page_size = max(1, min(int(page_size or limit), 50))
        safe_page = max(1, int(page))
        with self._connection() as conn, conn.cursor() as cur:
            self._ensure_schema(cur)
            cur.execute(
                """
                select count(*) as total
                from theme_research_reports
                """
            )
            total_row = cur.fetchone() or {}
            total = int(total_row.get("total") or 0)
            total_pages = max(1, math.ceil(total / safe_page_size)) if total else 1
            safe_page = min(safe_page, total_pages)
            offset = (safe_page - 1) * safe_page_size
            cur.execute(
                """
                select r.task_id, r.theme_name, r.created_at, r.updated_at, t.status
                from theme_research_reports r
                left join theme_research_tasks t on t.task_id = r.task_id
                order by r.updated_at desc
                limit %s offset %s
                """,
                (safe_page_size, offset),
            )
            rows = cur.fetchall() or []
        return {
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": total_pages,
            "items": [
                {
                    "task_id": str(row.get("task_id") or ""),
                    "theme_name": str(row.get("theme_name") or ""),
                    "status": str(row.get("status") or ""),
                    "created_at": str(row.get("created_at") or ""),
                    "updated_at": str(row.get("updated_at") or ""),
                }
                for row in rows
            ]
        }

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise ThemeResearchError("未配置 MySQL，题材研究模块暂时无法写入任务与报告。", 500)

    def _connection(self):
        return mysql_connection(self.dsn, connect_timeout_seconds=2.0)

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute(
            """
            create table if not exists theme_research_tasks (
              id bigint unsigned not null auto_increment primary key,
              task_id varchar(128) not null,
              theme_name varchar(128) not null,
              market varchar(32) not null default 'A股',
              analysis_depth varchar(32) not null default 'standard',
              time_horizon varchar(32) not null default '短中线',
              status varchar(32) not null default 'created',
              created_at datetime not null default current_timestamp,
              updated_at datetime not null default current_timestamp on update current_timestamp,
              unique key uk_theme_research_task_id (task_id),
              key idx_theme_research_status (status),
              key idx_theme_research_updated_at (updated_at)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        cur.execute(
            """
            create table if not exists theme_research_steps (
              id bigint unsigned not null auto_increment primary key,
              task_id varchar(128) not null,
              step_no int not null,
              step_title varchar(255) not null,
              event_type varchar(32) not null default 'step_update',
              status varchar(32) not null,
              message text,
              data_preview longtext,
              created_at datetime not null default current_timestamp,
              key idx_theme_research_steps_task (task_id),
              key idx_theme_research_steps_event (event_type),
              key idx_theme_research_steps_created_at (created_at)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        cur.execute(
            """
            create table if not exists theme_research_reports (
              id bigint unsigned not null auto_increment primary key,
              task_id varchar(128) not null,
              theme_name varchar(128) not null,
              report_json longtext not null,
              created_at datetime not null default current_timestamp,
              updated_at datetime not null default current_timestamp on update current_timestamp,
              unique key uk_theme_research_reports_task_id (task_id),
              key idx_theme_research_reports_updated_at (updated_at)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        self._schema_ready = True


class ThemeResearchService:
    def __init__(
        self,
        data_client: TushareClient | None = None,
        miaoxiang_client: EastMoneyMiaoxiangClient | None = None,
        agent: ThemeResearchAgent | None = None,
        credential_service: CredentialService | None = None,
        store: ThemeResearchStore | None = None,
        dsn: str | None = None,
        max_companies: int = 12,
    ):
        self.dsn = str(dsn or mysql_dsn_from_env() or "").strip()
        self.credential_service = credential_service
        self.data_client = data_client
        self.miaoxiang_client = miaoxiang_client
        self.agent = agent
        self.store = store or ThemeResearchStore(dsn=self.dsn)
        self.max_companies = max(4, min(int(max_companies), 20))
        self._worker_lock = threading.Lock()
        self._workers: dict[str, threading.Thread] = {}

    def start_task(
        self,
        theme_name: str,
        market: str = "A股",
        analysis_depth: str = "standard",
        time_horizon: str = "短中线",
    ) -> dict[str, Any]:
        clean_theme = str(theme_name or "").strip()
        if not clean_theme:
            raise ThemeResearchError("请输入行业、题材或概念名称。", 400)
        self._ensure_runtime()
        task_id = self._build_task_id()
        self.store.create_task(
            task_id=task_id,
            theme_name=clean_theme,
            market=str(market or "A股").strip() or "A股",
            analysis_depth=str(analysis_depth or "standard").strip() or "standard",
            time_horizon=str(time_horizon or "短中线").strip() or "短中线",
        )
        self.store.append_event(
            task_id=task_id,
            step_no=0,
            step_title="调研任务已创建",
            event_type="task_started",
            status="running",
            message=f"开始调研题材“{clean_theme}”。",
            data_preview=[],
        )
        worker = threading.Thread(
            target=self._run_task,
            args=(task_id, clean_theme, market, analysis_depth, time_horizon),
            daemon=True,
        )
        with self._worker_lock:
            self._workers[task_id] = worker
        worker.start()
        return {"task_id": task_id, "status": "created"}

    def event_stream(self, task_id: str):
        task = self.store.get_task(task_id)
        if not task:
            raise ThemeResearchError("未找到对应的题材研究任务。", 404)
        last_id = 0
        report_sent = False
        terminal_seen = False
        while True:
            steps = self.store.list_steps(task_id, after_id=last_id)
            for step in steps:
                last_id = max(last_id, int(step.get("id") or 0))
                yield _to_sse(step.get("event_type") or "step_update", _step_event_payload(step))

            report_payload = self.store.get_report(task_id)
            if report_payload and not report_sent:
                report_sent = True
                yield _to_sse(
                    "final_report",
                    {
                        "event_type": "final_report",
                        "task_id": task_id,
                        "status": "success",
                        "title": "最终报告生成完成",
                        "message": "题材研究报告已生成，可直接查看完整结论。",
                        "report": report_payload.get("report") or {},
                    },
                )

            task = self.store.get_task(task_id)
            if task and task.get("status") in {"completed", "failed"}:
                if terminal_seen and (report_sent or task.get("status") == "failed"):
                    break
                terminal_seen = True
            else:
                terminal_seen = False

            if not steps:
                yield ": ping\n\n"
                time.sleep(0.8)

    def get_report(self, task_id: str) -> dict[str, Any]:
        payload = self.store.get_report(task_id)
        if not payload:
            raise ThemeResearchError("当前任务还没有生成最终报告。", 404)
        task = self.store.get_task(task_id) or {}
        return {
            "task_id": task_id,
            "theme_name": payload.get("theme_name") or task.get("theme_name") or "",
            "status": task.get("status") or "",
            "report": payload.get("report") or {},
            "created_at": payload.get("created_at") or "",
            "updated_at": payload.get("updated_at") or "",
        }

    def list_reports(self, limit: int = 12, page: int = 1, page_size: int | None = None) -> dict[str, Any]:
        return self.store.list_reports(limit=limit, page=page, page_size=page_size)

    def _ensure_runtime(self) -> None:
        if self.data_client is not None and self.miaoxiang_client is not None and self.agent is not None:
            return
        try:
            credential_service = self.credential_service or CredentialService(dsn=self.dsn)
            deepseek_config = credential_service.get_deepseek_config()
            tushare_token = credential_service.get_tushare_token()
            miaoxiang_config = credential_service.get_miaoxiang_config()
        except CredentialServiceError as exc:
            raise ThemeResearchError(exc.message, exc.status_code) from exc

        if self.data_client is None:
            self.data_client = TushareClient(token=tushare_token)
        if self.miaoxiang_client is None:
            self.miaoxiang_client = EastMoneyMiaoxiangClient(api_key=miaoxiang_config["api_key"])
        if self.agent is None:
            self.agent = ThemeResearchAgent(**deepseek_config)

    def _run_task(self, task_id: str, theme_name: str, market: str, analysis_depth: str, time_horizon: str) -> None:
        self.store.update_task_status(task_id, "running")
        try:
            normalized = self._step_normalize(task_id, theme_name, market, analysis_depth, time_horizon)
            theme_events = self._step_theme_events(task_id, normalized)
            search_bundle = self._step_miaoxiang_search(task_id, normalized)
            tushare_bundle = self._step_tushare(task_id, normalized, search_bundle)
            scored_bundle = self._step_score_and_falsify(task_id, normalized, theme_events, search_bundle, tushare_bundle)
            report = self._step_generate_report(task_id, normalized, theme_events, search_bundle, tushare_bundle, scored_bundle)
            self.store.save_report(task_id=task_id, theme_name=theme_name, report_json=report)
            self.store.update_task_status(task_id, "completed")
        except (ThemeResearchError, DataProviderError, MXProviderError, AIProviderError) as exc:
            self.store.update_task_status(task_id, "failed")
            self.store.append_event(
                task_id=task_id,
                step_no=99,
                step_title="调研失败",
                event_type="task_failed",
                status="error",
                message=str(getattr(exc, "message", str(exc))),
                data_preview=[],
            )
        except Exception as exc:
            self.store.update_task_status(task_id, "failed")
            self.store.append_event(
                task_id=task_id,
                step_no=99,
                step_title="调研失败",
                event_type="task_failed",
                status="error",
                message=f"题材研究执行异常：{exc}",
                data_preview=[],
            )
        finally:
            with self._worker_lock:
                self._workers.pop(task_id, None)

    def _step_normalize(
        self,
        task_id: str,
        theme_name: str,
        market: str,
        analysis_depth: str,
        time_horizon: str,
    ) -> dict[str, Any]:
        self._emit_tool_started(task_id, 1, "题材标准化", "DeepSeek 正在识别题材关键词与标准名称。")
        result = self.agent.normalize_theme(theme_name=theme_name, market=market, analysis_depth=analysis_depth, time_horizon=time_horizon)
        normalized_name = str(result.get("normalized_name") or theme_name).strip() or theme_name
        keywords = [str(item).strip() for item in result.get("keywords", []) if str(item).strip()]
        if theme_name not in keywords:
            keywords.insert(0, theme_name)
        result["theme_name"] = theme_name
        result["normalized_name"] = normalized_name
        result["keywords"] = keywords[:8]
        preview = [
            {
                "title": "标准题材名",
                "source": "DeepSeek",
                "publish_time": "",
                "summary": normalized_name,
                "url": "",
                "evidence_level": "A",
            }
        ] + [
            {
                "title": keyword,
                "source": "DeepSeek",
                "publish_time": "",
                "summary": "题材关键词",
                "url": "",
                "evidence_level": "A",
            }
            for keyword in result["keywords"]
        ]
        self._emit_tool_finished(task_id, 1, "题材标准化", f"已识别关键词 {len(result['keywords'])} 个。", preview)
        self._emit_step(task_id, 1, "题材标准化", "success", f"标准题材名：{normalized_name}", preview)
        return result

    def _step_theme_events(self, task_id: str, normalized: dict[str, Any]) -> dict[str, Any]:
        theme_name = normalized.get("normalized_name") or normalized.get("theme_name") or ""
        self._emit_tool_started(task_id, 2, "妙想题材事件", f"正在检索“{theme_name}”的产业事件与政策催化。")
        result = self.miaoxiang_client.search_theme_events(str(theme_name))
        preview = (result.get("items") or [])[:6]
        message = f"共获取题材事件 {int(result.get('count') or len(preview))} 条。"
        self._emit_tool_finished(task_id, 2, "妙想题材事件", message, preview)
        self._emit_step(task_id, 2, "妙想题材事件查询", "success", message, preview)
        return result

    def _step_miaoxiang_search(self, task_id: str, normalized: dict[str, Any]) -> dict[str, Any]:
        theme_name = str(normalized.get("normalized_name") or normalized.get("theme_name") or "").strip()
        original_name = str(normalized.get("theme_name") or theme_name).strip()
        news = {"status": "error", "items": [], "count": 0, "message": ""}
        announcements = {"status": "error", "items": [], "count": 0, "message": ""}
        sentiment = {"status": "error", "items": [], "count": 0, "message": ""}
        related_stocks = {"status": "error", "items": [], "count": 0, "message": ""}

        for title, runner in (
            ("妙想新闻研报", lambda: self.miaoxiang_client.search_news(theme_name or original_name)),
            ("妙想公告检索", lambda: self.miaoxiang_client.search_announcements(theme_name or original_name)),
            ("妙想舆情检索", lambda: self.miaoxiang_client.search_sentiment(theme_name or original_name)),
            ("妙想相关股票", lambda: self.miaoxiang_client.search_related_stocks(theme_name or original_name)),
        ):
            self._emit_tool_started(task_id, 3, title, f"正在调用 {title}。")
            try:
                result = runner()
                preview = (result.get("items") or [])[:5]
                self._emit_tool_finished(task_id, 3, title, f"返回 {int(result.get('count') or len(preview))} 条记录。", preview)
                if "新闻" in title:
                    news = result
                elif "公告" in title:
                    announcements = result
                elif "舆情" in title:
                    sentiment = result
                else:
                    related_stocks = result
            except MXProviderError as exc:
                self.store.append_event(
                    task_id=task_id,
                    step_no=3,
                    step_title=title,
                    event_type="tool_call_failed",
                    status="error",
                    message=exc.message,
                    data_preview=[],
                )
                if "新闻" in title:
                    news["message"] = exc.message
                elif "公告" in title:
                    announcements["message"] = exc.message
                elif "舆情" in title:
                    sentiment["message"] = exc.message
                else:
                    related_stocks["message"] = exc.message

        preview = []
        preview.extend((announcements.get("items") or [])[:3])
        preview.extend((news.get("items") or [])[:3])
        if related_stocks.get("items"):
            preview.extend((related_stocks.get("items") or [])[:3])
        message = (
            f"新闻 {int(news.get('count') or 0)} 条，公告 {int(announcements.get('count') or 0)} 条，"
            f"舆情 {int(sentiment.get('count') or 0)} 条，相关股票 {int(related_stocks.get('count') or 0)} 家。"
        )
        status = "success" if preview else "partial"
        self._emit_step(task_id, 3, "妙想公告新闻舆情查询", status, message, preview[:10])
        return {
            "news": news,
            "announcements": announcements,
            "sentiment": sentiment,
            "related_stocks": related_stocks,
        }

    def _step_tushare(self, task_id: str, normalized: dict[str, Any], search_bundle: dict[str, Any]) -> dict[str, Any]:
        theme_name = str(normalized.get("normalized_name") or normalized.get("theme_name") or "").strip()
        related_stocks = search_bundle.get("related_stocks") or {}
        self._emit_tool_started(task_id, 4, "Tushare 题材映射", f"正在聚合“{theme_name}”的 A 股映射公司。")
        candidate_bundle = self._collect_candidate_stocks(theme_name, normalized.get("keywords") or [], related_stocks.get("items") or [])
        companies = candidate_bundle.get("companies") or []
        boards = candidate_bundle.get("boards") or []
        preview = [
            {
                "title": board.get("name") or "",
                "source": f"Tushare/{board.get('source_label') or board.get('source')}",
                "publish_time": board.get("trade_date") or "",
                "summary": f"题材板块命中，成分股 {board.get('member_count', 0)} 只。",
                "url": "",
                "evidence_level": "A",
            }
            for board in boards[:4]
        ]
        self._emit_tool_finished(task_id, 4, "Tushare 题材映射", f"命中板块 {len(boards)} 个，候选公司 {len(companies)} 家。", preview)

        top_list_payload = self.data_client.get_top_list()
        top_list_items = top_list_payload.get("items") or []

        snapshots = []
        total = len(companies)
        for index, company in enumerate(companies, start=1):
            snapshot = self._build_company_snapshot(company, top_list_items=top_list_items, theme_name=theme_name, keywords=normalized.get("keywords") or [])
            snapshots.append(snapshot)
            progress_preview = [
                {
                    "title": snapshot.get("stock", {}).get("name") or "",
                    "source": "Tushare",
                    "publish_time": snapshot.get("bak_basic", {}).get("trade_date") or "",
                    "summary": (
                        f"营收同比 {snapshot.get('bak_basic', {}).get('rev_yoy', '待核实')}，"
                        f"利润同比 {snapshot.get('bak_basic', {}).get('profit_yoy', '待核实')}，"
                        f"龙虎榜 {snapshot.get('top_list_count', 0)} 次。"
                    ),
                    "url": "",
                    "evidence_level": "A",
                }
            ]
            self._emit_step(
                task_id,
                4,
                "Tushare 结构化数据聚合",
                "running" if index < total else "success",
                f"结构化数据已完成 {index} / {total} 家。",
                progress_preview,
            )

        final_preview = [
            {
                "title": item.get("stock", {}).get("name") or "",
                "source": "Tushare",
                "publish_time": item.get("bak_basic", {}).get("trade_date") or "",
                "summary": f"板块映射 {len(item.get('board_refs') or [])} 条，资金摘要 {item.get('moneyflow_summary', {}).get('headline') or '待核实'}。",
                "url": "",
                "evidence_level": "A",
            }
            for item in snapshots[:8]
        ]
        self.store.append_event(
            task_id=task_id,
            step_no=4,
            step_title="Tushare 结构化数据聚合预览",
            event_type="data_preview",
            status="success",
            message=f"候选公司 {len(snapshots)} 家。",
            data_preview=final_preview,
        )
        return {
            "boards": boards,
            "companies": snapshots,
        }

    def _step_score_and_falsify(
        self,
        task_id: str,
        normalized: dict[str, Any],
        theme_events: dict[str, Any],
        search_bundle: dict[str, Any],
        tushare_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        companies = tushare_bundle.get("companies") or []
        sources = self._collect_sources(theme_events, search_bundle)
        company_cards = [
            self._evaluate_company(
                company=item,
                keywords=normalized.get("keywords") or [],
                sources=sources,
            )
            for item in companies
        ]
        scoring_table = [item["scoring"] for item in company_cards]
        company_layers = _build_company_layers(company_cards)
        falsification = _build_falsification(company_cards)
        preview = [
            {
                "title": row.get("company") or "",
                "source": "系统评分",
                "publish_time": "",
                "summary": f"综合 {row.get('total_score')} 分，结论：{row.get('qualitative')}",
                "url": "",
                "evidence_level": "A",
            }
            for row in scoring_table[:8]
        ]
        self._emit_step(
            task_id,
            5,
            "三步证伪与五维评分",
            "success",
            f"已完成 {len(scoring_table)} 家公司的证伪与评分。",
            preview,
        )
        return {
            "company_cards": company_cards,
            "scoring_table": scoring_table,
            "company_layers": company_layers,
            "falsification": falsification,
        }

    def _step_generate_report(
        self,
        task_id: str,
        normalized: dict[str, Any],
        theme_events: dict[str, Any],
        search_bundle: dict[str, Any],
        tushare_bundle: dict[str, Any],
        scored_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        facts = self._build_fact_packet(task_id, normalized, theme_events, search_bundle, tushare_bundle, scored_bundle)
        tree_facts = _build_industry_tree_prompt_facts(facts)
        mece_fallback_message = ""
        self._emit_tool_started(task_id, 6, "DeepSeek MECE拆分", "正在选择最优维度并生成题材行业树。")
        try:
            final_tree, final_quality = self._plan_industry_tree_with_quality(task_id, tree_facts, "DeepSeek MECE拆分")
            facts["industry_tree_plan"] = final_tree
            facts["industry_tree_plan_quality"] = final_quality
            tree_preview = _industry_tree_preview_rows(final_tree)
            final_status = "success"
            if not final_quality.get("is_valid"):
                final_status = "partial"
                mece_fallback_message = _industry_tree_quality_feedback(final_quality)
            self._emit_step(
                task_id,
                6,
                "MECE 行业拆分",
                final_status,
                _industry_tree_step_message("行业树拆分完成", final_quality),
                tree_preview,
            )
        except AIProviderError as exc:
            self.store.append_event(
                task_id=task_id,
                step_no=6,
                step_title="DeepSeek MECE拆分",
                event_type="tool_call_failed",
                status="error",
                message=f"{exc.message}，正在使用精简事实包重试。",
                data_preview=[],
            )
            self._emit_step(task_id, 6, "MECE 行业拆分", "running", f"{exc.message}，正在使用精简事实包重试。", [])
            retry_tree_facts = _build_industry_tree_retry_facts(facts)
            self._emit_tool_started(task_id, 6, "DeepSeek MECE重试", "首次返回空结果，正在使用精简事实包重试。")
            try:
                final_tree, final_quality = self._plan_industry_tree_with_quality(task_id, retry_tree_facts, "DeepSeek MECE重试")
                facts["industry_tree_plan"] = final_tree
                facts["industry_tree_plan_quality"] = final_quality
                tree_preview = _industry_tree_preview_rows(final_tree)
                final_status = "success"
                if not final_quality.get("is_valid"):
                    final_status = "partial"
                    mece_fallback_message = _industry_tree_quality_feedback(final_quality)
                self._emit_step(
                    task_id,
                    6,
                    "MECE 行业拆分",
                    final_status,
                    _industry_tree_step_message("行业树拆分完成", final_quality),
                    tree_preview,
                )
            except AIProviderError as retry_exc:
                mece_fallback_message = f"{retry_exc.message}，已回退到规则化行业树。"
                facts["industry_tree_plan"] = _fallback_industry_tree_from_facts(facts)
                facts["industry_tree_plan_quality"] = {
                    "is_valid": False,
                    "issues": [mece_fallback_message],
                    "top_level_count": len(facts["industry_tree_plan"].get("children") or []),
                    "leaf_count": len(_industry_tree_preview_rows(facts["industry_tree_plan"])),
                    "assigned_company_count": 0,
                    "reference_company_count": len(_collect_industry_tree_reference_keys(facts)),
                }
                tree_preview = _industry_tree_preview_rows(facts["industry_tree_plan"])
                self.store.append_event(
                    task_id=task_id,
                    step_no=6,
                    step_title="DeepSeek MECE重试",
                    event_type="tool_call_failed",
                    status="error",
                    message=mece_fallback_message,
                    data_preview=tree_preview,
                )
                self._emit_step(task_id, 6, "MECE 行业拆分", "partial", mece_fallback_message, tree_preview)

        self._emit_tool_started(task_id, 7, "DeepSeek 最终报告", "正在基于 MECE 行业树和结构化证据生成题材研究结论。")
        report_fallback_message = ""
        report_facts = dict(facts)
        plan_quality = facts.get("industry_tree_plan_quality") or {}
        report_facts["industry_tree_plan_quality"] = plan_quality
        report_facts["industry_tree_rebuild_required"] = not bool(plan_quality.get("is_valid"))
        report_facts["industry_tree_plan"] = (
            {}
            if report_facts["industry_tree_rebuild_required"]
            else _compact_industry_tree_for_prompt(facts.get("industry_tree_plan") or {})
        )
        report_facts["sources"] = (facts.get("sources") or [])[:12]
        try:
            report = self.agent.generate_report(report_facts)
        except AIProviderError as exc:
            report_fallback_message = f"{exc.message}，已回退到规则化事实报告。"
            self.store.append_event(
                task_id=task_id,
                step_no=7,
                step_title="DeepSeek 最终报告",
                event_type="tool_call_failed",
                status="error",
                message=report_fallback_message,
                data_preview=[],
            )
            report = _fallback_report_from_facts(facts)
        final_report = _coerce_report_schema(report, facts)
        preview = [
            {
                "title": "最终结论",
                "source": "DeepSeek" if not report_fallback_message else "规则化事实报告",
                "publish_time": "",
                "summary": "报告已生成，可查看 MECE 行业树、股票映射、评分表和最终结论。",
                "url": "",
                "evidence_level": "A",
            }
        ]
        if not report_fallback_message:
            self._emit_tool_finished(task_id, 7, "DeepSeek 最终报告", "最终报告生成完成。", preview)
            self._emit_step(task_id, 7, "最终报告生成", "success", "题材研究报告生成完成。", preview)
        else:
            self._emit_step(task_id, 7, "最终报告生成", "partial", report_fallback_message, preview)
        return final_report

    def _plan_industry_tree_with_quality(
        self,
        task_id: str,
        tree_facts: dict[str, Any],
        first_tool_title: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        industry_tree_plan = self.agent.plan_industry_tree(tree_facts)
        initial_quality = _assess_industry_tree_quality(industry_tree_plan, tree_facts)
        initial_preview = _industry_tree_preview_rows(industry_tree_plan)
        self._emit_tool_finished(
            task_id,
            6,
            first_tool_title,
            _industry_tree_step_message("初次拆分完成", initial_quality),
            initial_preview,
        )

        final_tree = industry_tree_plan
        final_quality = initial_quality
        if not initial_quality.get("is_valid"):
            self._emit_step(
                task_id,
                6,
                "MECE 行业拆分",
                "running",
                f"初次拆分覆盖不足，正在二次细化：{_industry_tree_quality_feedback(initial_quality)}",
                initial_preview,
            )
            self._emit_tool_started(task_id, 6, "DeepSeek MECE复核", "初次行业树过窄，正在补全一级方向与细分叶子。")
            try:
                refined_tree = self.agent.refine_industry_tree(tree_facts, industry_tree_plan, initial_quality)
                refined_quality = _assess_industry_tree_quality(refined_tree, tree_facts)
                if refined_quality.get("score", 0) >= initial_quality.get("score", 0):
                    final_tree = refined_tree
                    final_quality = refined_quality
                refined_preview = _industry_tree_preview_rows(final_tree)
                self._emit_tool_finished(
                    task_id,
                    6,
                    "DeepSeek MECE复核",
                    _industry_tree_step_message("二次细化完成", final_quality),
                    refined_preview,
                )
            except AIProviderError as exc:
                self.store.append_event(
                    task_id=task_id,
                    step_no=6,
                    step_title="DeepSeek MECE复核",
                    event_type="tool_call_failed",
                    status="error",
                    message=f"{exc.message}，已保留初次拆分结果。",
                    data_preview=initial_preview,
                )
        return final_tree, final_quality

    def _collect_candidate_stocks(self, theme_name: str, keywords: list[str], related_items: list[dict[str, Any]]) -> dict[str, Any]:
        board_matches = []
        seen_boards: set[tuple[str, str]] = set()
        for source, board_types in (
            ("dc", ("concept", "industry")),
            ("ths", ("theme", "concept", "industry")),
            ("tdx", ("concept", "industry")),
        ):
            for query in [theme_name] + [item for item in keywords if item and item != theme_name]:
                for board_type in board_types:
                    try:
                        hits = self.data_client.search_boards(source=source, query=query, board_type=board_type, limit=3)
                    except DataProviderError:
                        continue
                    for hit in hits:
                        key = (str(hit.get("source") or source), str(hit.get("ts_code") or "").upper())
                        if not key[1] or key in seen_boards:
                            continue
                        seen_boards.add(key)
                        board_matches.append(hit)
        board_matches = board_matches[:6]

        company_map: dict[str, dict[str, Any]] = {}
        for board in board_matches:
            source = str(board.get("source") or "").strip()
            ts_code = str(board.get("ts_code") or "").strip()
            if not source or not ts_code:
                continue
            try:
                members = self.data_client.get_board_members(source=source, ts_code=ts_code)
            except DataProviderError:
                continue
            board["member_count"] = len(members)
            for member in members[:20]:
                stock_code = str(member.get("con_code") or member.get("ts_code") or "").strip().upper()
                stock_name = str(member.get("name") or "").strip()
                if not stock_code:
                    continue
                company = company_map.setdefault(
                    stock_code,
                    {
                        "ts_code": stock_code,
                        "name": stock_name,
                        "board_refs": [],
                        "source": "tushare-board",
                    },
                )
                company["name"] = company["name"] or stock_name
                company["board_refs"].append(
                    {
                        "source": source,
                        "source_label": str(board.get("source_label") or source),
                        "board_ts_code": ts_code,
                        "board_name": str(board.get("name") or "").strip(),
                        "board_type": str(board.get("type_key") or board.get("idx_type") or "").strip(),
                    }
                )

        for item in related_items[:20]:
            stock_code = str(item.get("ts_code") or "").strip().upper()
            stock_name = str(item.get("name") or item.get("title") or "").strip()
            if not stock_code and stock_name:
                try:
                    resolved = self.data_client.resolve_stock(stock_name)
                    stock_code = resolved.ts_code
                    stock_name = resolved.name
                except DataProviderError:
                    continue
            if not stock_code:
                continue
            company = company_map.setdefault(
                stock_code,
                {
                    "ts_code": stock_code,
                    "name": stock_name,
                    "board_refs": [],
                    "source": "mx-related",
                },
            )
            company["name"] = company["name"] or stock_name

        companies = sorted(
            company_map.values(),
            key=lambda item: (len(item.get("board_refs") or []), item.get("name") or "", item.get("ts_code") or ""),
            reverse=True,
        )[: self.max_companies]
        return {"boards": board_matches, "companies": companies}

    def _build_company_snapshot(
        self,
        company: dict[str, Any],
        top_list_items: list[dict[str, Any]],
        theme_name: str,
        keywords: list[str],
    ) -> dict[str, Any]:
        ts_code = str(company.get("ts_code") or "").strip().upper()
        if not ts_code:
            return {"stock": {}, "errors": ["缺少股票代码。"]}

        try:
            stock = self.data_client.resolve_stock(ts_code)
        except DataProviderError:
            stock = None

        bak_basic = {}
        kline_summary = {}
        daily_basic = {}
        moneyflow_summary = {}
        fina_indicator = {}
        income = {}
        cashflow = {}
        balancesheet = {}
        stock_company = {}
        errors = []

        try:
            bak_basic = self.data_client.get_stock_bak_basic(ts_code)
        except DataProviderError as exc:
            errors.append(exc.message)

        try:
            recent_end = datetime.now().strftime("%Y%m%d")
            recent_start = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
            klines = self.data_client.get_klines(ts_code, "daily", recent_start, recent_end)
            kline_summary = _summarize_kline_rows(klines)
        except DataProviderError as exc:
            errors.append(exc.message)

        pro = self.data_client._client()
        for label, loader in (
            ("daily_basic", lambda: _fetch_latest_trade_row(pro, "daily_basic", ts_code, days=20)),
            ("moneyflow", lambda: _summarize_moneyflow(_fetch_range_rows(pro, "moneyflow", ts_code, days=20))),
            ("fina_indicator", lambda: _fetch_latest_report_row(pro, "fina_indicator", ts_code)),
            ("income", lambda: _fetch_latest_report_row(pro, "income", ts_code)),
            ("cashflow", lambda: _fetch_latest_report_row(pro, "cashflow", ts_code)),
            ("balancesheet", lambda: _fetch_latest_report_row(pro, "balancesheet", ts_code)),
            ("stock_company", lambda: _fetch_company_row(pro, ts_code)),
        ):
            try:
                payload = loader()
            except DataProviderError as exc:
                errors.append(exc.message)
                payload = {}
            if label == "daily_basic":
                daily_basic = payload
            elif label == "moneyflow":
                moneyflow_summary = payload
            elif label == "fina_indicator":
                fina_indicator = payload
            elif label == "income":
                income = payload
            elif label == "cashflow":
                cashflow = payload
            elif label == "balancesheet":
                balancesheet = payload
            else:
                stock_company = payload

        top_list_recent = [
            item
            for item in top_list_items
            if str(item.get("ts_code") or "").strip().upper() == ts_code
        ][:5]

        business_text = " ".join(
            filter(
                None,
                [
                    str(stock_company.get("main_business") or "").strip(),
                    str(stock_company.get("business_scope") or "").strip(),
                    str(stock_company.get("introduction") or "").strip(),
                    str(stock.industry or "").strip() if stock else "",
                    theme_name,
                    " ".join(str(item) for item in keywords[:6]),
                ],
            )
        )

        return {
            "stock": stock.as_dict() if stock else {"ts_code": ts_code, "name": str(company.get("name") or "").strip()},
            "board_refs": company.get("board_refs") or [],
            "bak_basic": bak_basic,
            "daily_basic": daily_basic,
            "kline_summary": kline_summary,
            "moneyflow_summary": moneyflow_summary,
            "fina_indicator": fina_indicator,
            "income": income,
            "cashflow": cashflow,
            "balancesheet": balancesheet,
            "stock_company": stock_company,
            "top_list_recent": top_list_recent,
            "top_list_count": len(top_list_recent),
            "business_text": business_text,
            "errors": errors,
        }

    def _evaluate_company(self, company: dict[str, Any], keywords: list[str], sources: list[dict[str, Any]]) -> dict[str, Any]:
        stock = company.get("stock") or {}
        stock_name = str(stock.get("name") or "").strip()
        board_refs = company.get("board_refs") or []
        business_text = str(company.get("business_text") or "").strip()
        bak_basic = company.get("bak_basic") or {}
        daily_basic = company.get("daily_basic") or {}
        cashflow = company.get("cashflow") or {}
        fina_indicator = company.get("fina_indicator") or {}
        kline_summary = company.get("kline_summary") or {}
        moneyflow_summary = company.get("moneyflow_summary") or {}
        top_list_count = int(company.get("top_list_count") or 0)

        anchor_type = "C"
        anchor_reason = "目前更像情绪映射，仍缺乏直接业务锚。"
        if board_refs:
            anchor_type = "B"
            anchor_reason = "命中真实题材板块成分，优先视作业务锚点候选。"
        elif any(token in business_text for token in ("参股", "持股", "投资")):
            anchor_type = "A"
            anchor_reason = "存在股权或投资映射，但主营锚定仍需核实。"

        keyword_hits = sum(1 for token in keywords if token and token in business_text)
        board_score = min(3, len(board_refs))
        rev_yoy = _safe_float(bak_basic.get("rev_yoy") or fina_indicator.get("q_sales_yoy") or fina_indicator.get("or_yoy"))
        profit_yoy = _safe_float(bak_basic.get("profit_yoy") or fina_indicator.get("q_dtprofit_yoy") or fina_indicator.get("netprofit_yoy"))
        gpr = _safe_float(bak_basic.get("gpr") or fina_indicator.get("grossprofit_margin"))
        npr = _safe_float(bak_basic.get("npr") or fina_indicator.get("netprofit_margin"))
        total_mv = _safe_float(daily_basic.get("total_mv") or bak_basic.get("total_mv"))
        turnover_rate = _safe_float(daily_basic.get("turnover_rate") or bak_basic.get("turnover_rate"))
        cashflow_value = _safe_float(cashflow.get("n_cashflow_act"))
        pct_20d = _safe_float(kline_summary.get("pct_change_20d"))
        moneyflow_value = _safe_float(moneyflow_summary.get("net_amount_5d"))
        source_count = sum(1 for item in sources if stock_name and stock_name in f"{item.get('title','')} {item.get('summary','')} {item.get('entity_name','')}")

        industry_relevance = _clamp_score(4 + board_score + keyword_hits + (2 if anchor_type == "B" else 1 if anchor_type == "A" else 0))
        scarcity = _clamp_score(4 + board_score + (1 if total_mv and total_mv < 800 else 0) + (1 if top_list_count > 0 else 0))
        localization_space = _clamp_score(5 + _keyword_bonus(sources, ("国产", "替代", "自主", "安全可控")) + (1 if any(word in business_text for word in ("半导体", "封装", "液冷", "芯片", "材料")) else 0))
        earnings_reality = _clamp_score(
            4
            + (1 if rev_yoy > 0 else 0)
            + (1 if profit_yoy > 0 else 0)
            + (1 if cashflow_value > 0 else 0)
            + (1 if gpr >= 20 else 0)
            + (1 if npr >= 8 else 0)
        )
        prosperity_certainty = _clamp_score(
            4
            + (1 if pct_20d > 0 else 0)
            + (1 if turnover_rate >= 3 else 0)
            + (1 if moneyflow_value > 0 else 0)
            + (1 if top_list_count > 0 else 0)
            + min(2, source_count)
        )
        total_score = round(
            industry_relevance * 0.25
            + scarcity * 0.25
            + localization_space * 0.20
            + earnings_reality * 0.20
            + prosperity_certainty * 0.10,
            2,
        )

        if total_score >= 8:
            qualitative = "核心产业链公司，可重点研究"
            conclusion = "核心"
        elif total_score >= 6:
            qualitative = "有逻辑，但需要验证订单/业绩"
            conclusion = "观察"
        elif total_score >= 4:
            qualitative = "偏概念或兑现较慢"
            conclusion = "情绪"
        else:
            qualitative = "情绪炒作或高风险"
            conclusion = "回避"

        announcement_result = _announcement_result_for_company(stock_name, sources)
        financial_result = _financial_result_for_company(rev_yoy, profit_yoy, cashflow_value, gpr, npr)
        revenue_result = _revenue_result_for_company(stock_name, sources)

        return {
            "stock": stock,
            "company": stock_name,
            "ts_code": str(stock.get("ts_code") or "").strip(),
            "anchor_type": anchor_type,
            "anchor_reason": anchor_reason,
            "industry_position": _industry_position_from_anchor(anchor_type, board_refs),
            "earnings_stage": _earnings_stage_from_results(announcement_result, financial_result),
            "risks": _company_risks(company, announcement_result, financial_result),
            "conclusion": conclusion,
            "announcement_result": announcement_result,
            "financial_result": financial_result,
            "revenue_result": revenue_result,
            "scoring": {
                "company": stock_name,
                "ts_code": str(stock.get("ts_code") or "").strip(),
                "industry_relevance": industry_relevance,
                "scarcity": scarcity,
                "localization_space": localization_space,
                "earnings_reality": earnings_reality,
                "prosperity_certainty": prosperity_certainty,
                "total_score": total_score,
                "qualitative": qualitative,
            },
        }

    def _build_fact_packet(
        self,
        task_id: str,
        normalized: dict[str, Any],
        theme_events: dict[str, Any],
        search_bundle: dict[str, Any],
        tushare_bundle: dict[str, Any],
        scored_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        company_cards = scored_bundle.get("company_cards") or []
        sources = self._collect_sources(theme_events, search_bundle)
        best_segments = [str(board.get("name") or "").strip() for board in (tushare_bundle.get("boards") or [])[:3] if str(board.get("name") or "").strip()]
        core_companies = [item.get("company") for item in company_cards[:5] if item.get("company")]
        sentiment_only = [item.get("company") for item in company_cards if item.get("anchor_type") == "C"][:5]
        average_score = _average([_safe_float(item.get("scoring", {}).get("total_score")) for item in company_cards])
        suitable_for = "暂时回避"
        if average_score >= 8:
            suitable_for = "中线趋势"
        elif average_score >= 6:
            suitable_for = "短线题材"
        elif average_score >= 4:
            suitable_for = "长期研究"

        return {
            "task_id": task_id,
            "theme_name": str(normalized.get("theme_name") or "").strip(),
            "normalized_name": str(normalized.get("normalized_name") or normalized.get("theme_name") or "").strip(),
            "keywords": normalized.get("keywords") or [],
            "stage_guess": str(normalized.get("stage_guess") or "").strip(),
            "current_drivers": normalized.get("current_drivers") or [],
            "theme_events": _compact_evidence_items(theme_events.get("items") or [], limit=8, summary_chars=120),
            "news_items": _compact_evidence_items((search_bundle.get("news") or {}).get("items") or [], limit=8, summary_chars=120),
            "announcement_items": _compact_evidence_items((search_bundle.get("announcements") or {}).get("items") or [], limit=8, summary_chars=140),
            "sentiment_items": _compact_evidence_items((search_bundle.get("sentiment") or {}).get("items") or [], limit=6, summary_chars=100),
            "related_stocks": _compact_stock_items((search_bundle.get("related_stocks") or {}).get("items") or [], limit=8),
            "board_matches": _compact_board_matches(tushare_bundle.get("boards") or [], limit=4),
            "company_cards": _compact_company_cards(company_cards, limit=12),
            "falsification_input": scored_bundle.get("falsification") or {},
            "scoring_table_input": scored_bundle.get("scoring_table") or [],
            "company_layers_input": scored_bundle.get("company_layers") or {},
            "final_conclusion_input": {
                "best_chain_segments": best_segments,
                "core_companies": core_companies,
                "sentiment_only_companies": sentiment_only,
                "suitable_for": suitable_for,
            },
            "sources": sources,
            "risk_disclaimer": "本报告仅供研究，不构成投资建议。",
        }

    def _collect_sources(self, theme_events: dict[str, Any], search_bundle: dict[str, Any]) -> list[dict[str, Any]]:
        items = []
        for bundle in (
            theme_events.get("items") or [],
            (search_bundle.get("news") or {}).get("items") or [],
            (search_bundle.get("announcements") or {}).get("items") or [],
            (search_bundle.get("sentiment") or {}).get("items") or [],
            (search_bundle.get("related_stocks") or {}).get("items") or [],
        ):
            for item in bundle:
                if not isinstance(item, dict):
                    continue
                items.append(
                    {
                        "title": str(item.get("title") or item.get("name") or "").strip(),
                        "source": str(item.get("source") or "东方财富妙想").strip(),
                        "publish_time": str(item.get("publish_time") or "").strip(),
                        "summary": _truncate_text(str(item.get("summary") or "").strip(), 140),
                        "url": str(item.get("url") or "").strip(),
                        "evidence_level": str(item.get("evidence_level") or "").strip() or "B",
                        "entity_name": str(item.get("entity_name") or item.get("name") or "").strip(),
                    }
                )
        return items[:24]

    def _emit_tool_started(self, task_id: str, step_no: int, step_title: str, message: str) -> None:
        self.store.append_event(
            task_id=task_id,
            step_no=step_no,
            step_title=step_title,
            event_type="tool_call_started",
            status="running",
            message=message,
            data_preview=[],
        )

    def _emit_tool_finished(self, task_id: str, step_no: int, step_title: str, message: str, preview: Any) -> None:
        self.store.append_event(
            task_id=task_id,
            step_no=step_no,
            step_title=step_title,
            event_type="tool_call_finished",
            status="success",
            message=message,
            data_preview=preview,
        )

    def _emit_step(self, task_id: str, step_no: int, step_title: str, status: str, message: str, preview: Any) -> None:
        self.store.append_event(
            task_id=task_id,
            step_no=step_no,
            step_title=step_title,
            event_type="step_update",
            status=status,
            message=message,
            data_preview=preview,
        )
        if preview:
            self.store.append_event(
                task_id=task_id,
                step_no=step_no,
                step_title=f"{step_title}预览",
                event_type="data_preview",
                status=status,
                message=message,
                data_preview=preview,
            )

    @staticmethod
    def _build_task_id(prefix: bool = True) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = uuid.uuid4().hex[:6]
        return f"{'theme_research_' if prefix else ''}{stamp}_{suffix}"


def _serialize_db_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {str(key): _json_safe_scalar(value) for key, value in row.items()}


def _serialize_step_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    payload = {str(key): _json_safe_scalar(value) for key, value in row.items()}
    try:
        payload["data_preview"] = json.loads(str(row.get("data_preview") or "[]"))
    except json.JSONDecodeError:
        payload["data_preview"] = []
    return payload


def _step_event_payload(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_type": step.get("event_type") or "step_update",
        "task_id": step.get("task_id") or "",
        "step": int(step.get("step_no") or 0),
        "status": step.get("status") or "",
        "title": step.get("step_title") or "",
        "message": step.get("message") or "",
        "data_preview": step.get("data_preview") or [],
        "created_at": step.get("created_at") or "",
    }


def _to_sse(event_name: str, payload: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _truncate_text(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:max(0, limit - 1)]}…"


def _compact_evidence_items(items: list[dict[str, Any]], limit: int = 8, summary_chars: int = 120) -> list[dict[str, Any]]:
    results = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": str(item.get("title") or item.get("name") or "").strip(),
                "source": str(item.get("source") or "东方财富妙想").strip(),
                "publish_time": str(item.get("publish_time") or "").strip(),
                "summary": _truncate_text(str(item.get("summary") or "").strip(), summary_chars),
                "evidence_level": str(item.get("evidence_level") or "").strip() or "B",
            }
        )
    return results


def _compact_stock_items(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    results = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "ts_code": str(item.get("ts_code") or "").strip(),
                "name": str(item.get("name") or item.get("title") or "").strip(),
                "summary": _truncate_text(str(item.get("summary") or "").strip(), 80),
                "evidence_level": str(item.get("evidence_level") or "").strip() or "A",
            }
        )
    return results


def _compact_board_matches(items: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    results = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "name": str(item.get("name") or "").strip(),
                "source": str(item.get("source_label") or item.get("source") or "").strip(),
                "trade_date": str(item.get("trade_date") or "").strip(),
                "member_count": int(item.get("member_count") or 0),
                "leading": str(item.get("leading") or "").strip(),
                "board_type": str(item.get("type_key") or item.get("idx_type") or "").strip(),
            }
        )
    return results


def _compact_company_cards(items: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    results = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "company": str(item.get("company") or "").strip(),
                "ts_code": str(item.get("ts_code") or "").strip(),
                "anchor_type": str(item.get("anchor_type") or "").strip() or "C",
                "anchor_reason": _truncate_text(str(item.get("anchor_reason") or "").strip(), 80),
                "industry_position": _truncate_text(str(item.get("industry_position") or "").strip(), 80),
                "earnings_stage": _truncate_text(str(item.get("earnings_stage") or "").strip(), 40),
                "risks": [_truncate_text(str(risk), 40) for risk in (item.get("risks") or [])[:3]],
                "conclusion": str(item.get("conclusion") or "").strip(),
                "announcement_result": item.get("announcement_result") or {},
                "financial_result": item.get("financial_result") or {},
                "revenue_result": item.get("revenue_result") or {},
                "scoring": item.get("scoring") or {},
            }
        )
    return results


def _build_industry_tree_prompt_facts(facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": facts.get("task_id") or "",
        "theme_name": facts.get("theme_name") or "",
        "normalized_name": facts.get("normalized_name") or "",
        "keywords": (facts.get("keywords") or [])[:8],
        "stage_guess": facts.get("stage_guess") or "",
        "current_drivers": (facts.get("current_drivers") or [])[:6],
        "theme_events": _compact_evidence_items(facts.get("theme_events") or [], limit=6, summary_chars=90),
        "news_items": _compact_evidence_items(facts.get("news_items") or [], limit=6, summary_chars=90),
        "board_matches": _compact_board_matches(facts.get("board_matches") or [], limit=5),
        "company_cards": _compact_company_cards(facts.get("company_cards") or [], limit=12),
        "final_conclusion_input": facts.get("final_conclusion_input") or {},
    }


def _build_industry_tree_retry_facts(facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": facts.get("task_id") or "",
        "theme_name": facts.get("theme_name") or "",
        "normalized_name": facts.get("normalized_name") or "",
        "keywords": (facts.get("keywords") or [])[:8],
        "stage_guess": facts.get("stage_guess") or "",
        "current_drivers": (facts.get("current_drivers") or [])[:4],
        "board_matches": _compact_board_matches(facts.get("board_matches") or [], limit=3),
        "company_cards": _compact_company_cards(facts.get("company_cards") or [], limit=10),
        "final_conclusion_input": facts.get("final_conclusion_input") or {},
    }


def _compact_industry_tree_for_prompt(industry_tree: dict[str, Any], max_children: int = 5, max_leaf_companies: int = 5) -> dict[str, Any]:
    if not isinstance(industry_tree, dict):
        return {}

    def compact_node(node: dict[str, Any], depth: int = 0) -> dict[str, Any]:
        payload = {
            "name": str(node.get("name") or "").strip(),
            "summary": str(node.get("summary") or "").strip(),
            "evidence_level": str(node.get("evidence_level") or "").strip() or "A",
        }
        children = [compact_node(child, depth + 1) for child in (node.get("children") or [])[:max_children] if isinstance(child, dict)]
        companies = []
        for company in (node.get("companies") or [])[:max_leaf_companies]:
            if not isinstance(company, dict):
                continue
            companies.append(
                {
                    "company_name": str(company.get("company_name") or "").strip(),
                    "stock_code": str(company.get("stock_code") or "").strip(),
                    "anchor_type": str(company.get("anchor_type") or "").strip() or "C",
                    "score": _safe_float(company.get("score")),
                }
            )
        if children:
            payload["children"] = children
        if companies:
            payload["companies"] = companies
        return payload

    return {
        "theme": str(industry_tree.get("theme") or "").strip(),
        "dimension": str(industry_tree.get("dimension") or "").strip(),
        "dimension_reason": str(industry_tree.get("dimension_reason") or "").strip(),
        "children": [compact_node(node) for node in (industry_tree.get("children") or [])[:max_children] if isinstance(node, dict)],
    }


def _collect_industry_tree_reference_keys(facts: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for item in facts.get("company_cards") or []:
        if not isinstance(item, dict):
            continue
        company_name = str(item.get("company") or item.get("company_name") or "").strip()
        stock_code = str(item.get("ts_code") or item.get("stock_code") or "").strip().upper()
        if stock_code or company_name:
            keys.add(stock_code or company_name)
    for item in facts.get("scoring_table_input") or []:
        if not isinstance(item, dict):
            continue
        company_name = str(item.get("company") or item.get("company_name") or "").strip()
        stock_code = str(item.get("ts_code") or item.get("stock_code") or "").strip().upper()
        if stock_code or company_name:
            keys.add(stock_code or company_name)
    return keys


def _collect_industry_tree_stats(industry_tree: dict[str, Any]) -> dict[str, Any]:
    assigned_keys: set[str] = set()
    leaf_count = 0
    empty_leaf_count = 0
    max_depth = 0

    def walk(nodes: list[dict[str, Any]], depth: int) -> None:
        nonlocal leaf_count, empty_leaf_count, max_depth
        for node in nodes:
            if not isinstance(node, dict):
                continue
            max_depth = max(max_depth, depth)
            companies = node.get("companies") or []
            for company in companies:
                if not isinstance(company, dict):
                    continue
                company_name = str(company.get("company_name") or "").strip()
                stock_code = str(company.get("stock_code") or "").strip().upper()
                if stock_code or company_name:
                    assigned_keys.add(stock_code or company_name)
            children = [child for child in (node.get("children") or []) if isinstance(child, dict)]
            if children:
                walk(children, depth + 1)
                continue
            leaf_count += 1
            if not companies:
                empty_leaf_count += 1

    children = [child for child in (industry_tree.get("children") or []) if isinstance(child, dict)]
    walk(children, 1)
    return {
        "top_level_count": len(children),
        "leaf_count": leaf_count,
        "empty_leaf_count": empty_leaf_count,
        "assigned_company_count": len(assigned_keys),
        "max_depth": max_depth,
    }


def _industry_tree_is_fallback(industry_tree: dict[str, Any]) -> bool:
    if not isinstance(industry_tree, dict):
        return True
    dimension = str(industry_tree.get("dimension") or "").strip()
    if "兜底" in dimension:
        return True
    top_names = {
        str(item.get("name") or "").strip()
        for item in (industry_tree.get("children") or [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    fallback_names = {"业务映射", "股权映射", "情绪映射"}
    return bool(top_names) and top_names.issubset(fallback_names)


def _assess_industry_tree_quality(industry_tree: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    stats = _collect_industry_tree_stats(industry_tree)
    reference_count = len(_collect_industry_tree_reference_keys(facts))
    keyword_count = len(facts.get("keywords") or [])
    min_top_level = 2 if reference_count or keyword_count >= 3 else 1
    min_leaf_count = 3 if reference_count >= 6 or keyword_count >= 5 else 2 if min_top_level >= 2 else 1
    min_assignments = 0
    if reference_count >= 8:
        min_assignments = 5
    elif reference_count >= 5:
        min_assignments = 3
    elif reference_count >= 3:
        min_assignments = 2

    issues = []
    if _industry_tree_is_fallback(industry_tree):
        issues.append("当前返回仍是业务/股权/情绪映射兜底，不是真正的行业 MECE 拆分")
    if stats["top_level_count"] < min_top_level:
        issues.append(f"一级方向只有 {stats['top_level_count']} 个，至少需要 {min_top_level} 个")
    if stats["leaf_count"] < min_leaf_count:
        issues.append(f"细分叶子只有 {stats['leaf_count']} 个，至少需要 {min_leaf_count} 个")
    if stats["max_depth"] < 2 and stats["top_level_count"]:
        issues.append("没有继续向下拆分到可读的细分层")
    if min_assignments and stats["assigned_company_count"] < min_assignments:
        issues.append(f"只挂接了 {stats['assigned_company_count']}/{reference_count} 家候选公司，覆盖偏窄")

    score = (
        stats["top_level_count"] * 4
        + stats["leaf_count"] * 2
        + stats["assigned_company_count"]
        + (4 if stats["max_depth"] >= 2 else 0)
    )
    if not issues:
        score += 6
    return {
        **stats,
        "reference_company_count": reference_count,
        "min_top_level": min_top_level,
        "min_leaf_count": min_leaf_count,
        "min_assignments": min_assignments,
        "issues": issues,
        "is_valid": not issues,
        "score": score,
    }


def _industry_tree_quality_feedback(quality_report: dict[str, Any]) -> str:
    issues = quality_report.get("issues") or []
    base = "；".join(str(item).strip() for item in issues if str(item).strip()) or "请补全行业树主干结构。"
    return (
        f"{base}。"
        f"当前为 {quality_report.get('top_level_count', 0)} 个一级方向、"
        f"{quality_report.get('leaf_count', 0)} 个细分叶子、"
        f"挂接 {quality_report.get('assigned_company_count', 0)}/"
        f"{quality_report.get('reference_company_count', 0)} 家候选公司。"
    )


def _industry_tree_step_message(prefix: str, quality_report: dict[str, Any]) -> str:
    summary = (
        f"{prefix}：{quality_report.get('top_level_count', 0)} 个一级方向，"
        f"{quality_report.get('leaf_count', 0)} 个细分叶子，"
        f"挂接 {quality_report.get('assigned_company_count', 0)}/"
        f"{quality_report.get('reference_company_count', 0)} 家候选公司。"
    )
    if quality_report.get("is_valid"):
        return summary
    return f"{summary} 当前仍有缺口，{_industry_tree_quality_feedback(quality_report)}"


def _fetch_latest_trade_row(pro: Any, api_name: str, ts_code: str, days: int = 20) -> dict[str, Any]:
    api = getattr(pro, api_name, None)
    if not callable(api):
        raise DataProviderError(f"Tushare 不支持接口：{api_name}", 502)
    last_error = None
    for offset in range(days):
        trade_date = (datetime.now() - timedelta(days=offset)).strftime("%Y%m%d")
        try:
            df = api(ts_code=ts_code, trade_date=trade_date)
        except Exception as exc:
            last_error = exc
            continue
        row = _latest_row(df)
        if row:
            return row
    if last_error:
        raise DataProviderError(f"Tushare {api_name} 获取失败：{last_error}", 502) from last_error
    return {}


def _fetch_range_rows(pro: Any, api_name: str, ts_code: str, days: int = 20) -> list[dict[str, Any]]:
    api = getattr(pro, api_name, None)
    if not callable(api):
        raise DataProviderError(f"Tushare 不支持接口：{api_name}", 502)
    start_date = (datetime.now() - timedelta(days=max(days, 5))).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")
    try:
        df = api(ts_code=ts_code, start_date=start_date, end_date=end_date)
    except TypeError:
        try:
            df = api(ts_code=ts_code)
        except Exception as exc:
            raise DataProviderError(f"Tushare {api_name} 获取失败：{exc}", 502) from exc
    except Exception as exc:
        raise DataProviderError(f"Tushare {api_name} 获取失败：{exc}", 502) from exc
    return _top_rows(df, limit=days, sort_columns=("trade_date",))


def _fetch_latest_report_row(pro: Any, api_name: str, ts_code: str) -> dict[str, Any]:
    api = getattr(pro, api_name, None)
    if not callable(api):
        raise DataProviderError(f"Tushare 不支持接口：{api_name}", 502)
    try:
        df = api(ts_code=ts_code)
    except Exception as exc:
        raise DataProviderError(f"Tushare {api_name} 获取失败：{exc}", 502) from exc
    return _latest_row(df, sort_columns=("end_date", "ann_date", "trade_date"))


def _fetch_company_row(pro: Any, ts_code: str) -> dict[str, Any]:
    api = getattr(pro, "stock_company", None)
    if not callable(api):
        raise DataProviderError("Tushare 不支持 stock_company 接口。", 502)
    try:
        df = api(ts_code=ts_code)
    except Exception as exc:
        raise DataProviderError(f"Tushare stock_company 获取失败：{exc}", 502) from exc
    return _latest_row(df, sort_columns=("ts_code",))


def _latest_row(df: Any, sort_columns: tuple[str, ...] = ("trade_date",)) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {}
    frame = df.fillna("")
    available_columns = [column for column in sort_columns if column in frame.columns]
    if available_columns:
        frame = frame.sort_values(list(available_columns), ascending=False)
    row = frame.iloc[0].to_dict()
    return {str(key): _json_safe_scalar(value) for key, value in row.items()}


def _top_rows(df: Any, limit: int = 6, sort_columns: tuple[str, ...] = ("trade_date",)) -> list[dict[str, Any]]:
    if df is None or getattr(df, "empty", True):
        return []
    frame = df.fillna("")
    available_columns = [column for column in sort_columns if column in frame.columns]
    if available_columns:
        frame = frame.sort_values(list(available_columns), ascending=False)
    rows = frame.head(limit).to_dict("records")
    return [{str(key): _json_safe_scalar(value) for key, value in row.items()} for row in rows]


def _summarize_kline_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    latest = rows[-1]
    previous_20 = rows[-21] if len(rows) > 20 else rows[0]
    amount_values = [_safe_float(item.get("amount")) for item in rows[-5:]]
    return {
        "latest_close": _safe_float(latest.get("close")),
        "latest_date": str(latest.get("date") or ""),
        "pct_change_20d": round((_safe_float(latest.get("close")) / max(_safe_float(previous_20.get("close")), 0.01) - 1) * 100, 2),
        "amount_avg_5d": round(_average(amount_values), 2),
        "high_60d": round(max(_safe_float(item.get("high")) for item in rows[-60:]), 2),
        "low_60d": round(min(_safe_float(item.get("low")) for item in rows[-60:]), 2),
    }


def _summarize_moneyflow(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    selected = rows[:5]
    net_amount = 0.0
    for row in selected:
        if "net_mf_amount" in row:
            net_amount += _safe_float(row.get("net_mf_amount"))
        else:
            net_amount += (
                _safe_float(row.get("buy_lg_amount"))
                + _safe_float(row.get("buy_elg_amount"))
                - _safe_float(row.get("sell_lg_amount"))
                - _safe_float(row.get("sell_elg_amount"))
            )
    headline = "近 5 日主力净流入偏强。" if net_amount > 0 else "近 5 日主力净流出，承接一般。"
    return {"net_amount_5d": round(net_amount, 2), "headline": headline}


def _mx_search_evidence_level(info_type: str) -> str:
    if info_type == "ANNOUNCEMENT":
        return "S"
    if info_type in {"REPORT", "NEWS"}:
        return "B"
    return "B"


def _normalize_ts_code(code: str, market: str = "") -> str:
    text = str(code or "").strip().upper()
    if "." in text:
        return text
    if str(market or "").strip().upper() == ".SH":
        return f"{text}.SH"
    if str(market or "").strip().upper() == ".SZ":
        return f"{text}.SZ"
    if text.startswith(("5", "6", "9")):
        return f"{text}.SH"
    return f"{text}.SZ"


def _json_safe_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def _safe_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _average(values: list[float]) -> float:
    cleaned = [value for value in values if value or value == 0]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _clamp_score(value: int | float) -> int:
    return max(1, min(int(round(value)), 10))


def _keyword_bonus(sources: list[dict[str, Any]], keywords: tuple[str, ...]) -> int:
    text = " ".join(
        f"{item.get('title','')} {item.get('summary','')}"
        for item in sources[:20]
    )
    return min(3, sum(1 for keyword in keywords if keyword and keyword in text))


def _announcement_result_for_company(stock_name: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    text = " ".join(
        f"{item.get('title','')} {item.get('summary','')}"
        for item in sources
        if item.get("evidence_level") == "S" and (not stock_name or stock_name in f"{item.get('title','')} {item.get('summary','')} {item.get('entity_name','')}")
    )
    if any(token in text for token in ("量产", "供货", "订单", "中标", "认证")):
        return {"result": "证伪通过", "summary": "公告层面出现量产、供货或客户认证证据。"}
    if any(token in text for token in ("研发", "送样", "验证", "测试")):
        return {"result": "部分通过，需观察", "summary": "公告更多停留在研发、送样或验证阶段。"}
    if any(token in text for token in ("风险提示", "澄清", "未形成收入", "无相关")):
        return {"result": "证伪失败，偏概念或高风险", "summary": "公告存在澄清或风险提示，实锚较弱。"}
    return {"result": "部分通过，需观察", "summary": "公告证据不足，当前仍需继续核实。"}


def _financial_result_for_company(rev_yoy: float, profit_yoy: float, cashflow_value: float, gpr: float, npr: float) -> dict[str, Any]:
    if rev_yoy > 0 and profit_yoy > 0 and cashflow_value > 0 and gpr >= 20:
        return {"result": "证伪通过", "summary": "营收、利润和现金流基本共振，财务兑现较好。"}
    if rev_yoy > 0 or profit_yoy > 0 or cashflow_value > 0:
        return {"result": "部分通过，需观察", "summary": "财务有亮点，但仍存在利润或现金流待确认项。"}
    if rev_yoy < 0 and profit_yoy < 0 and cashflow_value <= 0 and npr < 5:
        return {"result": "证伪失败，偏概念或高风险", "summary": "财务兑现较弱，利润与现金流承压。"}
    return {"result": "部分通过，需观察", "summary": "财务证据有限，暂不支持高确定性结论。"}


def _revenue_result_for_company(stock_name: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    text = " ".join(
        f"{item.get('title','')} {item.get('summary','')}"
        for item in sources
        if not stock_name or stock_name in f"{item.get('title','')} {item.get('summary','')} {item.get('entity_name','')}"
    )
    if any(token in text for token in ("营收占比", "收入占比", "批量供货", "量产爬坡")):
        return {"result": "证伪通过", "summary": "已有收入占比或放量线索，可继续核对财报。"}
    if any(token in text for token in ("送样", "验证", "小批量", "导入")):
        return {"result": "部分通过，需观察", "summary": "收入贡献仍在早期阶段，距离放量还有不确定性。"}
    return {"result": "部分通过，需观察", "summary": "缺少细分收入与利润贡献口径，当前以待核实处理。"}


def _industry_position_from_anchor(anchor_type: str, board_refs: list[dict[str, Any]]) -> str:
    if anchor_type == "B" and board_refs:
        return f"命中 {board_refs[0].get('board_name') or '题材板块'} 成分，属于业务映射前排候选。"
    if anchor_type == "A":
        return "更偏股权或参股映射，需要继续核对穿透比例与收益路径。"
    return "当前更接近情绪映射，产业链唯一性与兑现度偏弱。"


def _earnings_stage_from_results(announcement_result: dict[str, Any], financial_result: dict[str, Any]) -> str:
    announcement = str(announcement_result.get("result") or "")
    financial = str(financial_result.get("result") or "")
    if announcement == "证伪通过" and financial == "证伪通过":
        return "量产/业绩兑现"
    if announcement == "部分通过，需观察" or financial == "部分通过，需观察":
        return "研发/送样/小批量"
    return "估值透支或待核实"


def _company_risks(company: dict[str, Any], announcement_result: dict[str, Any], financial_result: dict[str, Any]) -> list[str]:
    risks = []
    if announcement_result.get("result") != "证伪通过":
        risks.append("公告实锚不足，需核实订单与客户。")
    if financial_result.get("result") != "证伪通过":
        risks.append("财务兑现仍需继续观察。")
    for error in (company.get("errors") or [])[:2]:
        if error:
            risks.append(str(error))
    return risks[:3]


def _build_company_layers(company_cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    layers = {
        "core_growth": [],
        "stable_value": [],
        "concept_elasticity": [],
        "sentiment_trap": [],
    }
    for item in company_cards:
        score = _safe_float((item.get("scoring") or {}).get("total_score"))
        payload = {
            "company_name": item.get("company") or "",
            "stock_code": item.get("ts_code") or "",
            "chain_role": item.get("industry_position") or "",
            "anchor_type": item.get("anchor_type") or "C",
            "industry_position": item.get("industry_position") or "",
            "earnings_realization": item.get("earnings_stage") or "",
            "risk_points": item.get("risks") or [],
            "conclusion": item.get("conclusion") or "观察",
        }
        if score >= 8 and item.get("anchor_type") == "B":
            layers["core_growth"].append(payload)
        elif score >= 6.2:
            layers["stable_value"].append(payload)
        elif score >= 4:
            layers["concept_elasticity"].append(payload)
        else:
            layers["sentiment_trap"].append(payload)
    return layers


def _build_falsification(company_cards: list[dict[str, Any]]) -> dict[str, Any]:
    announcement_check = []
    financial_check = []
    revenue_contribution_check = []
    results = []
    for item in company_cards[:8]:
        company_name = item.get("company") or ""
        announcement = item.get("announcement_result") or {}
        financial = item.get("financial_result") or {}
        revenue = item.get("revenue_result") or {}
        announcement_check.append({"company": company_name, **announcement})
        financial_check.append({"company": company_name, **financial})
        revenue_contribution_check.append({"company": company_name, **revenue})
        results.extend([announcement.get("result"), financial.get("result"), revenue.get("result")])

    if results and all(result == "证伪通过" for result in results):
        overall_result = "证伪通过"
    elif any(result == "证伪通过" for result in results) or any(result == "部分通过，需观察" for result in results):
        overall_result = "部分通过，需观察"
    else:
        overall_result = "证伪失败，偏概念或高风险"
    return {
        "announcement_check": announcement_check,
        "financial_check": financial_check,
        "revenue_contribution_check": revenue_contribution_check,
        "overall_result": overall_result,
    }


def _empty_report_schema() -> dict[str, Any]:
    return {
        "task_id": "string",
        "theme_name": "string",
        "normalized_name": "string",
        "keywords": ["string"],
        "industry_definition": {},
        "industry_tree": _empty_industry_tree_schema(),
        "falsification": {
            "announcement_check": [],
            "financial_check": [],
            "revenue_contribution_check": [],
            "overall_result": "部分通过，需观察",
        },
        "industry_chain_map": {"tier_0": {}, "tier_1": [], "tier_2": [], "tier_3": [], "tier_4": []},
        "anchor_classification": {"equity_anchor": [], "business_anchor": [], "sentiment_mapping": []},
        "core_questions": {},
        "prosperity_analysis": {},
        "company_layers": {"core_growth": [], "stable_value": [], "concept_elasticity": [], "sentiment_trap": []},
        "scoring_table": [],
        "final_conclusion": {
            "best_chain_segments": [],
            "core_companies": [],
            "sentiment_only_companies": [],
            "suitable_for": "长期研究",
        },
        "sources": [],
        "risk_disclaimer": "本报告仅供研究，不构成投资建议。",
    }


def _empty_industry_tree_schema() -> dict[str, Any]:
    return {
        "theme": "string",
        "dimension": "string",
        "dimension_reason": "string",
        "children": [
            {
                "name": "string",
                "summary": "string",
                "evidence_level": "A",
                "children": [
                    {
                        "name": "string",
                        "summary": "string",
                        "evidence_level": "A",
                        "companies": [
                            {
                                "company_name": "string",
                                "stock_code": "string",
                                "anchor_type": "A|B|C",
                                "chain_role": "string",
                                "score": 0,
                                "qualitative": "string",
                                "conclusion": "string",
                                "evidence_level": "A",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _coerce_report_schema(report: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report or {})
    payload["task_id"] = str(facts.get("task_id") or payload.get("task_id") or "")
    payload["theme_name"] = str(facts.get("theme_name") or payload.get("theme_name") or "")
    payload["normalized_name"] = str(facts.get("normalized_name") or payload.get("normalized_name") or payload["theme_name"])
    payload["keywords"] = payload.get("keywords") or facts.get("keywords") or []
    payload["industry_definition"] = payload.get("industry_definition") or {
        "terminal_system": "",
        "demand_source": "",
        "stage": str(facts.get("stage_guess") or "待核实"),
        "current_drivers": facts.get("current_drivers") or [],
    }
    payload["industry_tree"] = _normalize_industry_tree(
        payload.get("industry_tree") or facts.get("industry_tree_plan") or _fallback_industry_tree_from_facts(facts),
        facts,
    )
    payload["falsification"] = payload.get("falsification") or facts.get("falsification_input") or {}
    payload["industry_chain_map"] = payload.get("industry_chain_map") or {"tier_0": {}, "tier_1": [], "tier_2": [], "tier_3": [], "tier_4": []}
    payload["anchor_classification"] = payload.get("anchor_classification") or _anchor_classification_from_company_cards(facts.get("company_cards") or [])
    payload["core_questions"] = payload.get("core_questions") or {}
    payload["prosperity_analysis"] = payload.get("prosperity_analysis") or {}
    payload["company_layers"] = payload.get("company_layers") or facts.get("company_layers_input") or {}
    payload["scoring_table"] = payload.get("scoring_table") or facts.get("scoring_table_input") or []
    payload["final_conclusion"] = payload.get("final_conclusion") or facts.get("final_conclusion_input") or {}
    payload["sources"] = payload.get("sources") or facts.get("sources") or []
    payload["risk_disclaimer"] = "本报告仅供研究，不构成投资建议。"
    return payload


def _fallback_report_from_facts(facts: dict[str, Any]) -> dict[str, Any]:
    company_cards = facts.get("company_cards") or []
    board_matches = facts.get("board_matches") or []
    keywords = facts.get("keywords") or []
    tier_4 = []
    for item in company_cards[:12]:
        scoring = item.get("scoring") or {}
        tier_4.append(
            {
                "company_name": item.get("company") or "",
                "stock_code": item.get("ts_code") or "",
                "chain_role": item.get("industry_position") or "",
                "anchor_type": item.get("anchor_type") or "C",
                "earnings_realization": item.get("earnings_stage") or "",
                "evidence_level": "A" if (item.get("anchor_type") or "") in {"A", "B"} else "C",
                "qualitative": scoring.get("qualitative") or "",
                "待核实事项": item.get("risks") or [],
            }
        )

    return {
        "task_id": facts.get("task_id") or "",
        "theme_name": facts.get("theme_name") or "",
        "normalized_name": facts.get("normalized_name") or facts.get("theme_name") or "",
        "keywords": keywords,
        "industry_definition": {
            "terminal_system": f"{facts.get('normalized_name') or facts.get('theme_name') or ''}相关半导体与算力系统",
            "demand_source": "AI算力、高性能计算、存储与高密度集成需求",
            "stage": facts.get("stage_guess") or "待核实",
            "current_drivers": facts.get("current_drivers") or [],
        },
        "industry_tree": _fallback_industry_tree_from_facts(facts),
        "falsification": facts.get("falsification_input") or {},
        "industry_chain_map": {
            "tier_0": {
                "theme": facts.get("normalized_name") or facts.get("theme_name") or "",
                "stage": facts.get("stage_guess") or "待核实",
                "drivers": facts.get("current_drivers") or [],
            },
            "tier_1": [item.get("name") or "" for item in board_matches[:4] if item.get("name")],
            "tier_2": keywords[:6],
            "tier_3": [
                "先进封装工艺验证",
                "封装材料与设备配套",
                "客户认证与量产爬坡",
            ],
            "tier_4": tier_4,
        },
        "anchor_classification": _anchor_classification_from_company_cards(company_cards),
        "core_questions": {
            "value_location": "价值量集中在先进封装工艺能力、关键材料与高端客户导入。",
            "barrier": "壁垒来自工艺良率、设备能力、客户认证与量产稳定性。",
            "supply_constraint": "供给约束主要在先进封装产能、关键设备与材料配套。",
            "demand_driver": "需求由 AI 算力、高性能计算、HBM 与国产替代共同驱动。",
            "a_share_uniqueness": "A股映射以封测龙头、材料配套与局部设备机会为主。",
            "earnings_timeline": "研发到送样、再到量产和业绩兑现，仍需持续跟踪。",
        },
        "prosperity_analysis": {
            "volume": "扩产、订单、客户导入与排产节奏是核心观察项。",
            "price": "高端封装与关键材料具备一定议价，但仍受景气波动影响。",
            "competition": "行业在扩产与技术升级并行，需警惕同质化竞争和价格战。",
            "policy_capital": "国产替代、产业资本开支与政策扶持共同提升景气关注度。",
        },
        "company_layers": facts.get("company_layers_input") or {},
        "scoring_table": facts.get("scoring_table_input") or [],
        "final_conclusion": facts.get("final_conclusion_input") or {},
        "sources": facts.get("sources") or [],
        "risk_disclaimer": "本报告仅供研究，不构成投资建议。",
    }


def _industry_tree_preview_rows(industry_tree: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for node in (industry_tree.get("children") or [])[:6]:
        child_names = [str(child.get("name") or "").strip() for child in (node.get("children") or [])[:4] if str(child.get("name") or "").strip()]
        rows.append(
            {
                "title": str(node.get("name") or "待核实").strip(),
                "source": "DeepSeek / MECE 行业拆分",
                "publish_time": "",
                "summary": " / ".join(child_names) or str(node.get("summary") or "已完成一级拆分").strip() or "待核实",
                "url": "",
                "evidence_level": str(node.get("evidence_level") or "A").strip() or "A",
            }
        )
    return rows[:6]


def _fallback_industry_tree_from_facts(facts: dict[str, Any]) -> dict[str, Any]:
    company_cards = facts.get("company_cards") or []
    business = [item for item in company_cards if item.get("anchor_type") == "B"]
    equity = [item for item in company_cards if item.get("anchor_type") == "A"]
    sentiment = [item for item in company_cards if item.get("anchor_type") == "C"]
    groups = [
        ("业务映射", "核心业务落地与量产兑现", business),
        ("股权映射", "股权穿透与资产映射", equity),
        ("情绪映射", "概念扩散与交易情绪", sentiment),
    ]
    children = []
    for group_name, summary, items in groups:
        if not items:
            continue
        leaf_name = "核心公司" if group_name == "业务映射" else "重点映射"
        children.append(
            {
                "name": group_name,
                "summary": summary,
                "evidence_level": "A" if group_name != "情绪映射" else "C",
                "children": [
                    {
                        "name": leaf_name,
                        "summary": f"{group_name}下的候选映射",
                        "evidence_level": "A" if group_name != "情绪映射" else "C",
                        "companies": [
                            company_payload
                            for company_payload in (_company_card_to_industry_tree_company(item) for item in items[:8])
                            if company_payload
                        ],
                    }
                ],
            }
        )
    if not children:
        children = [
            {
                "name": str(facts.get("normalized_name") or facts.get("theme_name") or "题材主线"),
                "summary": "当前缺少可用拆分证据，暂以题材主线承载。",
                "evidence_level": "B",
                "children": [
                    {
                        "name": "待核实细分",
                        "summary": "等待更多公告、财务和产业链证据。",
                        "evidence_level": "B",
                        "companies": [],
                    }
                ],
            }
        ]
    return {
        "theme": str(facts.get("normalized_name") or facts.get("theme_name") or "题材研究").strip(),
        "dimension": "按映射性质兜底拆分",
        "dimension_reason": "当 MECE 行业树未成功生成时，先按业务/股权/情绪映射兜底展示，避免前端空白。",
        "children": children,
    }


def _normalize_industry_tree(industry_tree: Any, facts: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(industry_tree, dict):
        return _fallback_industry_tree_from_facts(facts)
    root = industry_tree.get("tree") if isinstance(industry_tree.get("tree"), dict) else industry_tree
    catalog = _build_industry_tree_company_catalog(facts)
    seen_company_keys: set[str] = set()
    children = []
    for node in root.get("children") or []:
        normalized = _normalize_industry_tree_node(node, catalog, seen_company_keys)
        if normalized:
            children.append(normalized)
    if not children:
        return _fallback_industry_tree_from_facts(facts)
    return {
        "theme": str(root.get("theme") or facts.get("normalized_name") or facts.get("theme_name") or "").strip(),
        "dimension": str(root.get("dimension") or root.get("split_dimension") or "待核实").strip() or "待核实",
        "dimension_reason": str(root.get("dimension_reason") or root.get("reason") or "待核实").strip() or "待核实",
        "children": children,
    }


def _normalize_industry_tree_node(node: Any, catalog: dict[str, dict[str, Any]], seen_company_keys: set[str]) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    name = str(node.get("name") or node.get("label") or node.get("segment") or node.get("title") or "").strip()
    if not name:
        return None
    children = []
    for child in node.get("children") or []:
        normalized_child = _normalize_industry_tree_node(child, catalog, seen_company_keys)
        if normalized_child:
            children.append(normalized_child)
    companies = []
    for item in node.get("companies") or node.get("stocks") or node.get("members") or []:
        normalized_company = _normalize_industry_tree_company(item, catalog, seen_company_keys)
        if normalized_company:
            companies.append(normalized_company)
    payload = {
        "name": name,
        "summary": str(node.get("summary") or node.get("description") or "待核实").strip() or "待核实",
        "evidence_level": str(node.get("evidence_level") or "A").strip() or "A",
    }
    if children:
        payload["children"] = children
    if companies:
        payload["companies"] = companies
    return payload


def _normalize_industry_tree_company(
    item: Any,
    catalog: dict[str, dict[str, Any]],
    seen_company_keys: set[str],
) -> dict[str, Any] | None:
    if isinstance(item, str):
        raw_name = str(item or "").strip()
        raw_code = ""
    elif isinstance(item, dict):
        raw_name = str(item.get("company_name") or item.get("company") or item.get("name") or "").strip()
        raw_code = str(item.get("stock_code") or item.get("ts_code") or "").strip().upper()
    else:
        return None
    fact = _lookup_industry_tree_company_fact(catalog, raw_name, raw_code)
    company_name = str(raw_name or fact.get("company_name") or "").strip()
    stock_code = str(raw_code or fact.get("stock_code") or "").strip().upper()
    if not company_name and not stock_code:
        return None
    dedupe_key = stock_code or company_name
    if dedupe_key in seen_company_keys:
        return None
    seen_company_keys.add(dedupe_key)
    score_value = _safe_float(item.get("score") if isinstance(item, dict) else None)
    if score_value is None:
        score_value = _safe_float(fact.get("score"))
    return {
        "company_name": company_name or stock_code,
        "stock_code": stock_code,
        "anchor_type": str((item.get("anchor_type") if isinstance(item, dict) else "") or fact.get("anchor_type") or "C").strip() or "C",
        "chain_role": str((item.get("chain_role") if isinstance(item, dict) else "") or fact.get("chain_role") or "").strip(),
        "score": score_value,
        "qualitative": str((item.get("qualitative") if isinstance(item, dict) else "") or fact.get("qualitative") or "").strip(),
        "conclusion": str((item.get("conclusion") if isinstance(item, dict) else "") or fact.get("conclusion") or "").strip(),
        "evidence_level": str((item.get("evidence_level") if isinstance(item, dict) else "") or fact.get("evidence_level") or "A").strip() or "A",
    }


def _build_industry_tree_company_catalog(facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for item in facts.get("company_cards") or []:
        _merge_industry_tree_company_fact(
            catalog,
            company_name=item.get("company") or "",
            stock_code=item.get("ts_code") or "",
            payload={
                "anchor_type": item.get("anchor_type") or "C",
                "chain_role": item.get("industry_position") or "",
                "qualitative": ((item.get("scoring") or {}).get("qualitative") or ""),
                "conclusion": item.get("conclusion") or "",
                "evidence_level": "A" if item.get("anchor_type") in {"A", "B"} else "C",
                "score": _safe_float((item.get("scoring") or {}).get("total_score")),
            },
        )
    for row in facts.get("scoring_table_input") or []:
        _merge_industry_tree_company_fact(
            catalog,
            company_name=row.get("company") or "",
            stock_code=row.get("ts_code") or "",
            payload={
                "qualitative": row.get("qualitative") or "",
                "score": _safe_float(row.get("total_score")),
            },
        )
    return catalog


def _merge_industry_tree_company_fact(
    catalog: dict[str, dict[str, Any]],
    company_name: Any,
    stock_code: Any,
    payload: dict[str, Any],
) -> None:
    name = str(company_name or "").strip()
    code = str(stock_code or "").strip().upper()
    if not name and not code:
        return
    key = code or name
    entry = catalog.get(key, {}).copy()
    if name:
        entry["company_name"] = name
    if code:
        entry["stock_code"] = code
    for field, value in payload.items():
        if value not in (None, "", []):
            entry[field] = value
    catalog[key] = entry
    if name:
        catalog[name] = entry
    if code:
        catalog[code] = entry


def _lookup_industry_tree_company_fact(catalog: dict[str, dict[str, Any]], company_name: str, stock_code: str) -> dict[str, Any]:
    if stock_code and stock_code in catalog:
        return catalog[stock_code]
    if company_name and company_name in catalog:
        return catalog[company_name]
    return {}


def _company_card_to_industry_tree_company(item: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    company_name = str(item.get("company") or "").strip()
    stock_code = str(item.get("ts_code") or "").strip().upper()
    if not company_name and not stock_code:
        return None
    scoring = item.get("scoring") or {}
    return {
        "company_name": company_name or stock_code,
        "stock_code": stock_code,
        "anchor_type": str(item.get("anchor_type") or "C").strip() or "C",
        "chain_role": str(item.get("industry_position") or "").strip(),
        "score": _safe_float(scoring.get("total_score")),
        "qualitative": str(scoring.get("qualitative") or "").strip(),
        "conclusion": str(item.get("conclusion") or "").strip(),
        "evidence_level": "A" if item.get("anchor_type") in {"A", "B"} else "C",
    }


def _anchor_classification_from_company_cards(company_cards: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {"equity_anchor": [], "business_anchor": [], "sentiment_mapping": []}
    for item in company_cards:
        payload = {
            "company_name": item.get("company") or "",
            "stock_code": item.get("ts_code") or "",
            "reason": item.get("anchor_reason") or "",
            "industry_position": item.get("industry_position") or "",
            "evidence_level": "A" if item.get("anchor_type") in {"A", "B"} else "C",
        }
        anchor_type = item.get("anchor_type")
        if anchor_type == "A":
            result["equity_anchor"].append(payload)
        elif anchor_type == "B":
            result["business_anchor"].append(payload)
        else:
            result["sentiment_mapping"].append(payload)
    return result
