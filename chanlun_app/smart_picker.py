from __future__ import annotations

import json
import re
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from .chanlun import analyze_klines
from .config import LEVELS, default_date_range
from .data_provider import DataProviderError, StockRecord, TushareClient
from .mx_provider import MXDataProvider, MXProviderError, _env_value
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
    _price_text,
    _signal_short_label,
    _latest_risk_card,
)


class MXWatchlistProvider(MXBaseClient):
    QUERY_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/get"
    MANAGE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/manage"

    def query(self) -> dict[str, Any]:
        result = self._post_json(self.QUERY_URL, {})
        if not isinstance(result, dict):
            raise MXProviderError("自选股查询返回格式异常。", 502)
        status = result.get("status")
        code = result.get("code")
        if status not in (0, "0", None) and code not in (0, "0", None):
            raise MXProviderError(f"自选股查询失败：{result.get('message') or status or code}", 502)

        data = result.get("data", {})
        inner = data.get("allResults", {}).get("result", {}) if isinstance(data, dict) else {}
        columns = inner.get("columns", []) if isinstance(inner, dict) else []
        data_list = inner.get("dataList", []) if isinstance(inner, dict) else []
        if not isinstance(columns, list) or not isinstance(data_list, list):
            raise MXProviderError("自选股查询数据结构异常。", 502)
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
        if not isinstance(result, dict):
            raise MXProviderError("自选股操作返回格式异常。", 502)
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

    def manage_group(self, action: str, target: str, group_name: str) -> dict[str, Any]:
        cleaned_action = (action or "").strip().lower()
        cleaned_target = (target or "").strip()
        cleaned_group = (group_name or "").strip()
        if cleaned_action not in {"add", "delete"}:
            raise MXProviderError("分组自选操作只支持 add 或 delete。", 400)
        if not cleaned_target:
            raise MXProviderError("缺少自选股代码或名称。", 400)
        if not cleaned_group:
            raise MXProviderError("缺少自选股组名称。", 400)

        eastmoney_header = _env_value("EASTMONEY_HEADER")
        eastmoney_appkey = _env_value("EASTMONEY_APPKEY")
        if eastmoney_header and eastmoney_appkey:
            return self._manage_group_with_eastmoney_web(
                action=cleaned_action,
                target=cleaned_target,
                group_name=cleaned_group,
                header_text=eastmoney_header,
                appkey=eastmoney_appkey,
            )

        if cleaned_action == "add":
            create_result = self._post_json(self.MANAGE_URL, {"query": f"创建自选股组{cleaned_group}"})
            if not _mx_manage_succeeded(create_result):
                raise MXProviderError(f"创建东方财富分组失败：{_mx_manage_result_text(create_result)}", 502)

        if cleaned_action == "add":
            queries = [
                f"把{cleaned_target}添加到{cleaned_group}自选股组",
                f"把{cleaned_target}加入{cleaned_group}分组",
            ]
        else:
            queries = [
                f"把{cleaned_target}从{cleaned_group}自选股组删除",
                f"把{cleaned_target}从{cleaned_group}分组移除",
            ]

        last_error = ""
        for query in queries:
            try:
                result = self._post_json(self.MANAGE_URL, {"query": query})
            except MXProviderError as exc:
                last_error = exc.message
                continue
            if not isinstance(result, dict):
                last_error = "自选股分组操作返回格式异常。"
                continue
            status = result.get("status")
            code = result.get("code")
            if status not in (0, "0", None) and code not in (0, "0", None):
                last_error = f"自选分组操作失败：{_mx_manage_result_text(result)}"
                continue
            if cleaned_action == "add" and not _mx_manage_group_confirmed(result, cleaned_group):
                raise MXProviderError(
                    f"接口已返回成功，但未确认写入分组“{cleaned_group}”：{_mx_manage_result_text(result)}",
                    502,
                )
            return {
                "status": "ok",
                "action": cleaned_action,
                "target": cleaned_target,
                "group_name": cleaned_group,
                "message": _mx_manage_success_text(result),
            }

        raise MXProviderError(last_error or "自选分组操作失败。", 502)

    def _manage_group_with_eastmoney_web(
        self,
        action: str,
        target: str,
        group_name: str,
        header_text: str,
        appkey: str,
    ) -> dict[str, Any]:
        if action != "add":
            raise MXProviderError("东方财富分组直连当前只支持加入操作。", 400)
        headers = _eastmoney_header_dict(header_text)
        if not headers:
            raise MXProviderError("EASTMONEY_HEADER 格式不正确，请从浏览器复制完整请求头。", 500)
        groups = self._eastmoney_get_groups(headers=headers, appkey=appkey)
        group_id = _eastmoney_find_group_id(groups, group_name)
        created = False
        if not group_id:
            created_payload = self._eastmoney_web_request(
                "ag",
                {"gn": group_name},
                headers=headers,
                appkey=appkey,
            )
            created = True
            group_id = str((created_payload.get("data") or {}).get("gid") or "")
            if not group_id:
                groups = self._eastmoney_get_groups(headers=headers, appkey=appkey)
                group_id = _eastmoney_find_group_id(groups, group_name)
        if not group_id:
            raise MXProviderError(f"东方财富分组“{group_name}”创建失败，未执行加入。", 502)

        stock_code = _eastmoney_stock_code(target)
        add_payload = self._eastmoney_web_request(
            "as",
            {"g": group_id, "sc": stock_code},
            headers=headers,
            appkey=appkey,
        )
        return {
            "status": "ok",
            "action": action,
            "target": target,
            "group_name": group_name,
            "group_id": group_id,
            "group_created": created,
            "message": _flatten((add_payload.get("data") or {}).get("msg") or add_payload.get("message") or "操作成功"),
            "source": "eastmoney-web",
        }

    def _eastmoney_get_groups(self, headers: dict[str, str], appkey: str) -> list[dict[str, Any]]:
        payload = self._eastmoney_web_request("ggdefstkindexinfos", {"g": "1"}, headers=headers, appkey=appkey)
        data = payload.get("data") or {}
        groups = data.get("ginfolist") or []
        return groups if isinstance(groups, list) else []

    def _eastmoney_web_request(
        self,
        action: str,
        params: dict[str, Any],
        headers: dict[str, str],
        appkey: str,
    ) -> dict[str, Any]:
        timestamp = int(time.time() * 1000)
        callback = f"jQuery112404771026622113468_{timestamp - 10}"
        query = {"appkey": appkey, "cb": callback, **params, "_": timestamp}
        url = f"https://myfavor.eastmoney.com/v4/webouter/{action}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise MXProviderError(f"东方财富分组请求失败：HTTP {exc.code}", 502) from exc
        except urllib.error.URLError as exc:
            raise MXProviderError(f"东方财富分组网络访问失败：{exc.reason}", 502) from exc
        payload = _parse_eastmoney_jsonp(raw)
        if not payload.get("state"):
            raise MXProviderError(_flatten(payload.get("message") or payload.get("msg") or "东方财富分组操作失败。"), 502)
        return payload


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
        self._stock_index_cache: dict[str, dict[str, Any]] | None = None
        self.trading_profile = trading_profile or TradingProfileService(
            mx_data_provider=self.mx_data_provider,
            news_provider=self.news_provider,
            screen_provider=self.screen_provider,
        )

    def overview(self) -> dict[str, Any]:
        market_cards = self._market_cards()
        news = self._safe_news("A股 今日 主流板块 政策 催化 最新公告")
        stage = _market_stage(market_cards)
        theme_context = self._build_theme_context(self._market_theme_rows(market_cards))
        return {
            "status": "ok",
            "stage": stage,
            "universe": self._universe(),
            "market_cards": market_cards,
            "theme_ladders": theme_context.get("groups", []),
            "leader_board": theme_context.get("leaders", []),
            "news": news,
        }

    def screen(self, query_text: str, level: str = "daily", limit: int = 20) -> dict[str, Any]:
        return self.screen_with_scopes(query_text=query_text, level=level, limit=limit, board_filters=None)

    def screen_with_board(
        self,
        query_text: str,
        level: str = "daily",
        limit: int = 20,
        board_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.screen_with_scopes(
            query_text=query_text,
            level=level,
            limit=limit,
            board_filters=[board_filter] if board_filter else None,
        )

    def screen_with_scopes(
        self,
        query_text: str,
        level: str = "daily",
        limit: int = 20,
        board_filters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        cleaned_query = (query_text or "").strip()
        if level not in LEVELS:
            raise MXProviderError(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        board_contexts = self._resolve_board_filters(board_filters or [])
        if cleaned_query:
            parsed = self.screen_provider.parse_response(self.screen_provider.search(cleaned_query))
            scoped_rows = self._apply_board_scope(parsed.get("rows", []), board_contexts)
            description = parsed.get("description", "")
            parser_text = parsed.get("parser_text", "")
            source_total = parsed.get("total", len(parsed.get("rows", [])))
        elif board_contexts:
            parsed = {"rows": [], "total": 0}
            scoped_rows = self._rows_from_board_contexts(board_contexts)
            description = "按板块成分股直接生成候选池。"
            parser_text = ""
            source_total = len(scoped_rows)
        else:
            raise MXProviderError("至少输入一种查询方式：条件、东方财富、通达信或同花顺。", 400)
        market_cards = self._market_cards()
        stage = _market_stage(market_cards)
        theme_context = self._build_theme_context(scoped_rows)

        candidates = []
        errors = []
        for row in scoped_rows[:limit]:
            try:
                candidates.append(self._candidate_from_row(row, level, stage, theme_context))
            except (DataProviderError, MXProviderError) as exc:
                errors.append({"row": row, "message": getattr(exc, "message", str(exc))})

        return {
            "status": "ok",
            "query_text": cleaned_query,
            "level": level,
            "level_label": LEVELS[level]["label"],
            "universe": self._universe(),
            "description": description,
            "parser_text": parser_text,
            "source_total": source_total,
            "total": len(scoped_rows),
            "stage": stage,
            "theme_ladders": theme_context.get("groups", []),
            "leader_board": theme_context.get("leaders", []),
            "theme_sample_size": theme_context.get("sample_size", 0),
            "board_filter": board_contexts[0].get("public", {}) if board_contexts else None,
            "board_filters": [item.get("public", {}) for item in board_contexts],
            "candidates": candidates,
            "errors": errors,
        }

    def screen_watchlist(self, level: str = "daily", limit: int | None = None) -> dict[str, Any]:
        if level not in LEVELS:
            raise MXProviderError(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        watchlist = self.watchlist()
        rows = self._rows_from_watchlist(watchlist.get("items", []))
        market_cards = self._market_cards()
        stage = _market_stage(market_cards)
        theme_context = self._build_theme_context(self._market_theme_rows(market_cards))

        scan_rows = rows if limit is None else rows[:limit]
        candidates = []
        errors = []
        fallback_count = 0
        for row in scan_rows:
            try:
                candidates.append(self._candidate_from_row(row, level, stage, theme_context))
            except (DataProviderError, MXProviderError) as exc:
                message = getattr(exc, "message", str(exc))
                fallback = self._fallback_candidate_from_row(row, level, stage, theme_context, message)
                if fallback:
                    candidates.append(fallback)
                    fallback_count += 1
                errors.append({"row": row, "message": message})

        return {
            "status": "ok",
            "source_type": "watchlist",
            "query_text": "",
            "level": level,
            "level_label": LEVELS[level]["label"],
            "universe": self._universe(),
            "description": "已把东方财富自选股同步为候选池，按当前结构级别做自选分析。",
            "parser_text": "",
            "source_total": watchlist.get("total", len(rows)),
            "total": len(rows),
            "stage": stage,
            "theme_ladders": theme_context.get("groups", []),
            "leader_board": theme_context.get("leaders", []),
            "theme_sample_size": theme_context.get("sample_size", 0),
            "board_filter": None,
            "board_filters": [],
            "watchlist": {
                "status": watchlist.get("status"),
                "label": watchlist.get("label", "我的自选"),
                "total": watchlist.get("total", len(rows)),
            },
            "fallback_count": fallback_count,
            "candidates": candidates,
            "errors": errors,
        }

    def candidate_detail(self, stock: dict[str, Any], level: str = "daily") -> dict[str, Any]:
        query = _flatten(stock.get("ts_code") or stock.get("symbol") or stock.get("name")).strip()
        if not query:
            raise MXProviderError("缺少候选股代码或名称。", 400)
        if level not in LEVELS:
            raise MXProviderError(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        try:
            stock_record = self.data_client.resolve_stock(query)
        except DataProviderError as exc:
            symbol = _flatten(stock.get("symbol") or query).strip()
            name = _flatten(stock.get("name") or query).strip()
            if not symbol and not name:
                raise
            stock_record = StockRecord(
                ts_code=_flatten(stock.get("ts_code") or symbol or name).strip(),
                symbol=symbol,
                name=name or symbol,
                industry=_flatten(stock.get("industry") or "").strip(),
                area=_flatten(stock.get("area") or "").strip(),
                market=_flatten(stock.get("market") or "").strip(),
                exchange=_flatten(stock.get("exchange") or "").strip(),
                list_date=_flatten(stock.get("list_date") or "").strip(),
                cnspell=_flatten(stock.get("cnspell") or "").strip(),
            )
            watchlist, in_watchlist, watchlist_row = self._watchlist_state(stock_record)
            return self._fallback_candidate_detail(stock_record, level, exc.message, watchlist, in_watchlist, watchlist_row)
        watchlist, in_watchlist, watchlist_row = self._watchlist_state(stock_record)
        start_date, end_date = default_date_range(level)
        try:
            klines = self.data_client.get_klines(stock_record.ts_code, level, start_date, end_date)
        except DataProviderError as exc:
            return self._fallback_candidate_detail(stock_record, level, exc.message, watchlist, in_watchlist, watchlist_row)
        analysis = analyze_klines(klines, level=level)
        analysis["stock"] = stock_record.as_dict()
        analysis["query"] = {
            "level": level,
            "level_label": LEVELS[level]["label"],
            "start_date": start_date,
            "end_date": end_date,
        }
        market_cards = self._market_cards()
        stage = _market_stage(market_cards)
        theme_context = self._build_theme_context(self._market_theme_rows(market_cards))
        market_row = _match_market_row(stock_record.as_dict(), market_cards) or watchlist_row
        emotion = _candidate_emotion(stock_record.as_dict(), market_row or {}, theme_context)
        leader = _candidate_leader(stock_record.as_dict(), market_row or {}, theme_context)
        capacity = _candidate_capacity(market_row or {})
        profile = self.trading_profile.build(stock=stock_record.as_dict(), analysis=analysis)
        execution = _build_execution_loop(
            stock=stock_record.as_dict(),
            analysis=analysis,
            profile_payload=profile.get("profile", {}) if isinstance(profile, dict) else {},
            stage=stage,
            emotion=emotion,
            leader=leader,
            capacity=capacity,
            quote_row=market_row or {},
        )
        return {
            "status": "ok",
            "stock": stock_record.as_dict(),
            "analysis": {
                "trend": analysis.get("trend", {}),
                "signals": analysis.get("signals", [])[-3:],
                "divergences": analysis.get("divergences", [])[-3:],
                "risk_cards": analysis.get("risk_cards", [])[-3:],
                "backtest": {
                    "summary": (analysis.get("backtest") or {}).get("summary", {}),
                    "trades": ((analysis.get("backtest") or {}).get("trades") or [])[-5:],
                    "note": (analysis.get("backtest") or {}).get("note", ""),
                },
                "level_context": analysis.get("level_context", {}),
            },
            "profile": profile,
            "execution": execution,
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

    def manage_watchlist_group(self, action: str, target: str, group_name: str) -> dict[str, Any]:
        return self.watchlist_provider.manage_group(action=action, target=target, group_name=group_name)

    def batch_manage_watchlist(self, action: str, targets_text: str, group_name: str = "") -> dict[str, Any]:
        cleaned_action = (action or "").strip().lower()
        cleaned_group = (group_name or "").strip()
        targets = _parse_watchlist_targets(targets_text)
        if cleaned_action not in {"add_group", "delete"}:
            raise MXProviderError("批量自选操作只支持 add_group 或 delete。", 400)
        if not targets:
            raise MXProviderError("缺少股票名称或代码。", 400)

        results = []
        success_count = 0
        fail_count = 0
        for target in targets:
            try:
                if cleaned_action == "add_group":
                    if cleaned_group:
                        payload = self.manage_watchlist_group("add", target, cleaned_group)
                    else:
                        payload = self.manage_watchlist("add", target)
                else:
                    payload = self.manage_watchlist("delete", target)
                success_count += 1
                results.append({"target": target, "status": "ok", "message": payload.get("message", "操作成功")})
            except (DataProviderError, MXProviderError) as exc:
                fail_count += 1
                results.append({"target": target, "status": "error", "message": getattr(exc, "message", str(exc))})

        status = "ok" if fail_count == 0 else "partial" if success_count > 0 else "error"
        if cleaned_action == "add_group":
            action_label = f"加入东方财富自选组“{cleaned_group}”" if cleaned_group else "加入东方财富自选"
        else:
            action_label = "删除东方财富自选"
        if status == "ok":
            message = f"{action_label}完成：共处理 {success_count} 只。"
        elif status == "partial":
            message = f"{action_label}部分完成：成功 {success_count} 只，失败 {fail_count} 只。"
        else:
            message = f"{action_label}失败：共 {fail_count} 只未处理成功。"

        return {
            "status": status,
            "action": cleaned_action,
            "group_name": cleaned_group,
            "total": len(targets),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
            "message": message,
        }

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
            "sample_rows": parsed.get("rows", [])[:36],
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

    def _candidate_from_row(
        self,
        row: dict[str, Any],
        level: str,
        stage: dict[str, Any],
        theme_context: dict[str, Any],
    ) -> dict[str, Any]:
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
        emotion = _candidate_emotion(stock.as_dict(), row, theme_context)
        capacity = _candidate_capacity(row)
        leader = _candidate_leader(stock.as_dict(), row, theme_context)
        overall = _candidate_overall(structure, emotion, capacity, leader, stage)

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
            "leader": leader,
            "overall": overall,
            "screen_row": row,
        }

    def _fallback_candidate_from_row(
        self,
        row: dict[str, Any],
        level: str,
        stage: dict[str, Any],
        theme_context: dict[str, Any],
        message: str,
    ) -> dict[str, Any] | None:
        query = (
            _row_value(row, ["股票代码", "代码"])
            or _row_value(row, ["股票简称", "名称"])
            or _row_value(row, ["股票名称", "名称"])
        )
        if not query:
            return None

        try:
            stock = self.data_client.resolve_stock(query)
            stock_payload = stock.as_dict()
        except DataProviderError:
            stock_payload = {
                "ts_code": _row_value(row, ["股票代码", "代码"]) or query,
                "symbol": _row_value(row, ["股票代码", "代码"]) or query,
                "name": _row_value(row, ["股票简称", "股票名称", "名称"]) or query,
                "industry": "",
                "area": "",
                "market": "",
                "exchange": "",
                "list_date": "",
                "cnspell": "",
            }

        structure = {
            "score": 35,
            "label": "结构待补充",
            "tone": "neutral",
            "summary": f"{LEVELS[level]['label']} · 当前环境暂缺结构数据，先展示自选行情。",
            "signal": message,
            "divergence": "",
            "invalidation_price": None,
            "unavailable": True,
        }
        emotion = _candidate_emotion(stock_payload, row, theme_context)
        capacity = _candidate_capacity(row)
        leader = _candidate_leader(stock_payload, row, theme_context)
        overall = _candidate_overall(structure, emotion, capacity, leader, stage)
        overall["label"] = "候选观察"
        overall["tone"] = "neutral"
        overall["decision"] = "自选已同步，先看行情与主流位置；补齐结构数据后再升级判断。"

        return {
            "stock": stock_payload,
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
            "leader": leader,
            "overall": overall,
            "screen_row": row,
            "analysis_available": False,
            "error_message": message,
        }

    def _market_cards(self) -> list[dict[str, Any]]:
        return [
            self._market_card("market_limit_up", "涨停强度", "今日涨停的A股"),
            self._market_card("market_heat", "高涨幅热度", "今日涨幅大于5%的A股"),
            self._market_card("market_liquidity", "活跃成交", "成交额大于10亿的A股"),
            self._market_card("market_limit_down", "跌停压力", "今日跌停的A股"),
            self._market_card("market_pressure", "下跌承压", "今日跌幅大于5%的A股"),
        ]

    @staticmethod
    def _market_theme_rows(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for card in cards:
            if card.get("key") not in {"market_limit_up", "market_heat", "market_liquidity"}:
                continue
            rows.extend(card.get("sample_rows", []))
        return rows

    def _build_theme_context(self, rows: list[dict[str, Any]], sample_limit: int = 120) -> dict[str, Any]:
        groups: dict[str, dict[str, Any]] = {}
        sample_rows = rows[:sample_limit]
        seen: set[str] = set()
        for row in sample_rows:
            stock = self._resolve_theme_stock(row)
            if not stock:
                continue
            industry = _flatten(stock.get("industry") or "").strip() or "行业待定"
            symbol = _flatten(stock.get("symbol") or "").strip()
            ts_code = _flatten(stock.get("ts_code") or "").strip()
            name = _flatten(stock.get("name") or "").strip()
            stock_key = ts_code or symbol or name
            if stock_key in seen:
                continue
            seen.add(stock_key)
            amount_value = _parse_numeric(_row_value(row, ["成交额", "成交金额"]))
            turnover_value = _parse_numeric(_row_value(row, ["换手率"]))
            change_value = _parse_numeric(_row_value(row, ["涨跌幅"]))
            group = groups.setdefault(
                industry,
                {"industry": industry, "members": [], "sample_count": 0, "strong_count": 0, "active_count": 0, "limit_up_count": 0},
            )
            member = {
                "symbol": symbol,
                "ts_code": ts_code,
                "name": name,
                "industry": industry,
                "change_pct_value": change_value,
                "change_pct": _row_value(row, ["涨跌幅"]),
                "amount_value": amount_value,
                "amount": _row_value(row, ["成交额", "成交金额"]),
                "turnover_value": turnover_value,
                "turnover": _row_value(row, ["换手率"]),
            }
            group["members"].append(member)
            group["sample_count"] += 1
            if change_value >= 5:
                group["strong_count"] += 1
            if amount_value >= 1_000_000_000:
                group["active_count"] += 1
            if change_value >= 9.5:
                group["limit_up_count"] += 1

        prepared = []
        for industry, group in groups.items():
            members = group["members"]
            if not members:
                continue
            avg_change = sum(item["change_pct_value"] for item in members) / len(members)
            total_amount = sum(item["amount_value"] for item in members)
            tier_score = (
                len(members) * 12
                + avg_change * 4
                + group["strong_count"] * 10
                + group["active_count"] * 7
                + group["limit_up_count"] * 14
            )
            members_by_strength = sorted(
                members,
                key=lambda item: (item["change_pct_value"], item["amount_value"], item["turnover_value"]),
                reverse=True,
            )
            members_by_amount = sorted(
                members,
                key=lambda item: (item["amount_value"], item["change_pct_value"], item["turnover_value"]),
                reverse=True,
            )
            dragon = members_by_strength[0]
            capacity_core = members_by_amount[0] if members_by_amount else dragon
            front_runners = members_by_strength[:3]
            if tier_score >= 78 or (len(members) >= 3 and group["strong_count"] >= 2 and group["active_count"] >= 2):
                tier_label = "主流热点"
                tone = "positive"
            elif tier_score >= 42 or (len(members) >= 2 and group["active_count"] >= 1):
                tier_label = "次主流"
                tone = "neutral"
            else:
                tier_label = "轮动观察"
                tone = "neutral"

            roles: dict[str, dict[str, Any]] = {}
            dragon_key = dragon["ts_code"] or dragon["symbol"] or dragon["name"]
            roles[dragon_key] = {
                "label": "龙头候选",
                "tone": "positive" if tier_label == "主流热点" else "neutral",
                "score": 84 if tier_label == "主流热点" else 70,
                "summary": f"{industry}样本中强度居前，辨识度最高，适合作为板块风向标观察。",
            }
            capacity_key = capacity_core["ts_code"] or capacity_core["symbol"] or capacity_core["name"]
            if capacity_key not in roles:
                roles[capacity_key] = {
                    "label": "容量中军",
                    "tone": "positive" if capacity_core["amount_value"] >= 1_000_000_000 else "neutral",
                    "score": 76 if capacity_core["amount_value"] >= 1_000_000_000 else 62,
                    "summary": f"{industry}里成交承接更足，适合当容量与承接的观察样本。",
                }
            for front in front_runners[1:3]:
                front_key = front["ts_code"] or front["symbol"] or front["name"]
                if front_key in roles:
                    continue
                roles[front_key] = {
                    "label": "前排助攻",
                    "tone": "neutral",
                    "score": 66,
                    "summary": f"{industry}梯队里的前排跟随股，强度还在，但辨识度次于龙头。",
                }

            prepared.append(
                {
                    "industry": industry,
                    "tier_label": tier_label,
                    "tone": tone,
                    "score": round(tier_score, 1),
                    "sample_count": len(members),
                    "avg_change_pct": round(avg_change, 2),
                    "active_count": group["active_count"],
                    "strong_count": group["strong_count"],
                    "limit_up_count": group["limit_up_count"],
                    "total_amount": total_amount,
                    "summary": f"{industry}样本 {len(members)} 只，平均涨幅 {avg_change:.2f}%，活跃承接 {group['active_count']} 只。",
                    "dragon": _theme_member_snapshot(dragon),
                    "capacity_core": _theme_member_snapshot(capacity_core),
                    "front_runners": [_theme_member_snapshot(item) for item in front_runners],
                    "roles": roles,
                }
            )

        prepared.sort(
            key=lambda item: (item["score"], item["active_count"], item["avg_change_pct"], item["sample_count"]),
            reverse=True,
        )
        groups_by_industry = {item["industry"]: item for item in prepared}
        leaders = []
        for item in prepared[:6]:
            leaders.append(
                {
                    "industry": item["industry"],
                    "tier_label": item["tier_label"],
                    "tone": item["tone"],
                    "role": "龙头候选",
                    "stock": item["dragon"],
                    "summary": item["summary"],
                }
            )
            if item["capacity_core"]["symbol"] != item["dragon"]["symbol"]:
                leaders.append(
                    {
                        "industry": item["industry"],
                        "tier_label": item["tier_label"],
                        "tone": item["tone"],
                        "role": "容量中军",
                        "stock": item["capacity_core"],
                        "summary": f"{item['industry']}里的容量承接代表，适合观察分歧后的承接力度。",
                    }
                )

        return {"groups": prepared[:6], "groups_by_industry": groups_by_industry, "leaders": leaders[:8], "sample_size": len(seen)}

    def _resolve_board_filters(self, board_filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        contexts = []
        for payload in board_filters:
            if not payload:
                continue
            source = _flatten(payload.get("source") or "dc").strip().lower()
            query = _flatten(payload.get("name") or payload.get("query") or payload.get("ts_code")).strip()
            if not query:
                continue
            board_type = _flatten(payload.get("board_type") or payload.get("idx_type")).strip()
            matches = self.data_client.search_boards(source=source, query=query, board_type=board_type, limit=12)
            if not matches:
                source_label = _board_source_label(source)
                raise DataProviderError(f"未找到{source_label}板块或概念：{query}", 404)

            normalized_query = query.upper()
            chosen = next(
                (
                    item
                    for item in matches
                    if normalized_query in {str(item.get("ts_code", "")).upper(), str(item.get("name", "")).upper()}
                ),
                matches[0],
            )
            members = self.data_client.get_board_members(source=source, ts_code=chosen.get("ts_code", ""))
            member_codes = {str(item.get("con_code", "")).upper() for item in members if item.get("con_code")}
            member_codes.update(str(item.get("symbol", "")).upper() for item in members if item.get("symbol"))
            member_names = {str(item.get("name", "")).strip() for item in members if item.get("name")}
            public = {
                "source": source,
                "source_label": chosen.get("source_label", _board_source_label(source)),
                "ts_code": chosen.get("ts_code", ""),
                "name": chosen.get("name", ""),
                "idx_type": chosen.get("idx_type", ""),
                "type_key": chosen.get("type_key", ""),
                "trade_date": chosen.get("trade_date", ""),
                "member_total": len(members),
            }
            contexts.append({"public": public, "member_codes": member_codes, "member_names": member_names, "members": members})
        return contexts

    @staticmethod
    def _apply_board_scope(rows: list[dict[str, Any]], board_contexts: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if not board_contexts:
            return list(rows)
        member_codes: set[str] = set()
        member_names: set[str] = set()
        for context in board_contexts:
            member_codes.update(context.get("member_codes") or set())
            member_names.update(context.get("member_names") or set())
        scoped = []
        for row in rows:
            code = _row_value(row, ["股票代码", "代码"]).strip().upper()
            name = _row_value(row, ["股票简称", "股票名称", "名称"]).strip()
            if code in member_codes or name in member_names or f"{code}.SZ" in member_codes or f"{code}.SH" in member_codes:
                scoped.append(row)
        return scoped

    def _rows_from_board_contexts(self, board_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for context in board_contexts:
            for member in context.get("members") or []:
                query = member.get("con_code") or member.get("symbol") or member.get("name") or ""
                try:
                    stock = self.data_client.resolve_stock(query)
                except DataProviderError:
                    continue
                if stock.ts_code in seen:
                    continue
                seen.add(stock.ts_code)
                rows.append(
                    {
                        "股票代码": stock.symbol,
                        "股票简称": stock.name,
                        "股票名称": stock.name,
                        "最新价": "",
                        "涨跌幅": "",
                        "成交额": "",
                        "换手率": "",
                        "__source_scope": context.get("public", {}).get("name", ""),
                        "__source_label": context.get("public", {}).get("source_label", ""),
                    }
                )
        return rows

    def _watchlist_state(self, stock_record: StockRecord) -> tuple[dict[str, Any], bool, dict[str, Any]]:
        try:
            watchlist = self.watchlist()
            matched_item = self._match_watchlist_item(watchlist.get("items", []), stock_record)
            in_watchlist = matched_item is not None
            return watchlist, in_watchlist, self._watchlist_item_row(matched_item)
        except Exception as exc:
            message = getattr(exc, "message", "") or str(exc) or "自选同步失败。"
            return {"status": "error", "message": message, "items": [], "total": 0}, False, {}

    @staticmethod
    def _match_watchlist_item(items: list[dict[str, Any]], stock_record: StockRecord) -> dict[str, Any] | None:
        for item in items or []:
            code = _flatten(item.get("code") or "").strip().upper()
            name = _flatten(item.get("name") or "").strip()
            if code in {stock_record.symbol.upper(), stock_record.ts_code.split(".")[0].upper()}:
                return item
            if name and name == stock_record.name:
                return item
        return None

    def _watchlist_item_row(self, item: dict[str, Any] | None) -> dict[str, Any]:
        rows = self._rows_from_watchlist([item] if item else [])
        return rows[0] if rows else {}

    def _rows_from_watchlist(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
            row = dict(raw)
            if not _row_value(row, ["股票代码", "代码"]):
                row["股票代码"] = _flatten(item.get("code") or item.get("ts_code") or "")
            if not _row_value(row, ["股票简称", "股票名称", "名称"]):
                row["股票简称"] = _flatten(item.get("name") or "")
            if not _row_value(row, ["最新价"]):
                row["最新价"] = _flatten(item.get("latest_price") or "")
            if not _row_value(row, ["涨跌幅"]):
                row["涨跌幅"] = _flatten(item.get("change_pct") or "")
            if not _row_value(row, ["换手率"]):
                row["换手率"] = _flatten(item.get("turnover") or "")
            if not _row_value(row, ["量比"]):
                row["量比"] = _flatten(item.get("volume_ratio") or "")

            query_key = (
                _row_value(row, ["股票代码", "代码"])
                or _row_value(row, ["股票简称", "股票名称", "名称"])
            ).strip()
            if not query_key:
                continue
            dedupe_key = query_key.upper()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            row["__source_scope"] = "我的自选"
            row["__source_label"] = "东方财富自选"
            rows.append(row)
        return rows

    def _fallback_candidate_detail(
        self,
        stock_record: StockRecord,
        level: str,
        message: str,
        watchlist: dict[str, Any],
        in_watchlist: bool,
        watchlist_row: dict[str, Any],
    ) -> dict[str, Any]:
        market_cards = self._market_cards()
        stage = _market_stage(market_cards)
        theme_context = self._build_theme_context(self._market_theme_rows(market_cards))
        market_row = _match_market_row(stock_record.as_dict(), market_cards) or watchlist_row
        emotion = _candidate_emotion(stock_record.as_dict(), market_row or {}, theme_context)
        leader = _candidate_leader(stock_record.as_dict(), market_row or {}, theme_context)
        capacity = _candidate_capacity(market_row or {})
        return {
            "status": "ok",
            "stock": stock_record.as_dict(),
            "analysis": {
                "unavailable": True,
                "message": message,
                "trend": {"label": "结构待补充", "position_label": "等待结构数据"},
                "signals": [],
                "divergences": [],
                "risk_cards": [],
                "backtest": {"summary": {}, "trades": [], "note": "当前环境缺少结构数据，复盘统计暂不展示。"},
                "level_context": {},
            },
            "profile": {
                "profile": {
                    "stance": "neutral",
                    "stance_label": "候选观察",
                    "headline": "自选股已同步，但当前环境暂缺缠论结构数据。",
                    "decision": "先把它放在观察位，补齐 Tushare 结构数据后再升级判断。",
                    "conclusion": "当前先依据自选行情、主流梯队和容量信息观察，不直接下执行结论。",
                    "tags": ["自选同步", "结构待补充"],
                },
                "mx_summary": {"status": "empty", "data": {"cards": []}},
                "news": {"status": "empty", "items": []},
                "market_scan": {"status": "empty", "cards": []},
            },
            "execution": {
                "plan": {
                    "title": "交易计划",
                    "setup": "数据待补充",
                    "tone": "neutral",
                    "verdict": "先观察",
                    "summary": f"{stock_record.name} 已进入自选候选池，但当前缺少 {LEVELS[level]['label']} 结构数据。",
                    "action": "先观察行情、热点与容量，不在结构信息缺失时提前下执行判断。",
                    "position_hint": "不执行，先补数据。",
                    "basis": [message, f"主流梯队：{emotion.get('label') or '未归类'}", f"容量情况：{capacity.get('label') or '待判断'}"],
                    "watch_points": ["补齐 Tushare 数据后再看买卖点。", "先看热点位置和承接，不把自选本身当成买入理由。"],
                    "avoid_if": ["结构数据未恢复前，不做执行升级。"],
                },
                "discipline": {
                    "title": "纪律引擎",
                    "score": 40,
                    "tone": "neutral",
                    "label": "先补数据",
                    "position_hint": "观察仓或空仓",
                    "summary": "当前环境缺少结构数据，纪律引擎先保持观察状态。",
                    "next_step": "补齐 Tushare 结构数据后，再检查买点、失效价和风报比。",
                    "checks": [
                        {"label": "结构数据是否可用", "passed": False, "detail": message},
                        {"label": "主流位置是否可跟踪", "passed": emotion.get("label") in {"主流热点", "次主流"}, "detail": f"当前归类为 {emotion.get('label') or '未归类'}。"},
                        {"label": "容量信息是否可参考", "passed": bool(market_row), "detail": capacity.get("summary") or "当前仅有有限行情字段。"},
                    ],
                },
                "review": {
                    "title": "复盘系统",
                    "label": "结构缺失",
                    "tone": "neutral",
                    "summary": "先把自选同步回来，等结构数据恢复后再补复盘样本和执行结论。",
                    "lessons": ["自选同步不应因为结构数据缺失而整页空白。"],
                    "recent_cases": [],
                    "note": "当前详情页先提供观察框架，避免因为单一数据源缺失直接中断工作流。",
                },
            },
            "watchlist": {
                "status": watchlist.get("status"),
                "in_watchlist": in_watchlist,
                "total": watchlist.get("total", 0),
            },
        }

    def _resolve_theme_stock(self, row: dict[str, Any]) -> dict[str, Any] | None:
        code = _row_value(row, ["股票代码", "代码"])
        short_name = _row_value(row, ["股票简称"])
        name = _row_value(row, ["股票名称", "名称"])
        query = code or short_name or name
        if not query:
            return None
        stock_index = self._stock_index()
        for key in [code.upper(), short_name, name]:
            if key and key in stock_index:
                return stock_index[key]
        try:
            stock = self.data_client.resolve_stock(query)
        except DataProviderError:
            return None
        return stock.as_dict()

    def _stock_index(self) -> dict[str, dict[str, Any]]:
        if self._stock_index_cache is not None:
            return self._stock_index_cache
        self._stock_index_cache = {}
        load_stocks = getattr(self.data_client, "load_stocks", None)
        if not callable(load_stocks):
            return self._stock_index_cache
        try:
            stocks = load_stocks()
        except DataProviderError:
            return self._stock_index_cache
        for _, row in stocks.iterrows():
            getter = row.get if hasattr(row, "get") else row.__getitem__
            stock = {
                "ts_code": str(getter("ts_code", "")),
                "symbol": str(getter("symbol", "")),
                "name": str(getter("name", "")),
                "area": str(getter("area", "")),
                "industry": str(getter("industry", "")),
                "market": str(getter("market", "")),
                "exchange": str(getter("exchange", "")),
                "list_date": str(getter("list_date", "")),
                "cnspell": str(getter("cnspell", "")),
            }
            for key in [stock["ts_code"].upper(), stock["symbol"].upper(), stock["name"]]:
                if key:
                    self._stock_index_cache[key] = stock
        return self._stock_index_cache


def _market_stage(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {item.get("key"): item for item in cards}
    limit_up = _safe_int((by_key.get("market_limit_up") or {}).get("total"))
    rise = _safe_int((by_key.get("market_heat") or {}).get("total"))
    active = _safe_int((by_key.get("market_liquidity") or {}).get("total"))
    limit_down = _safe_int((by_key.get("market_limit_down") or {}).get("total"))
    pressure = _safe_int((by_key.get("market_pressure") or {}).get("total"))

    score = 0
    if limit_up >= 40:
        score += 2
    elif limit_up >= 18:
        score += 1
    if rise >= 80:
        score += 2
    elif rise >= 40:
        score += 1
    if active >= 160:
        score += 2
    elif active >= 80:
        score += 1
    if limit_down >= 15:
        score -= 2
    elif limit_down >= 6:
        score -= 1
    if pressure >= 60:
        score -= 2
    elif pressure >= 30:
        score -= 1

    if score >= 4:
        label = "主流活跃"
        tone = "positive"
        cycle = "主升试错期"
        action = "养家视角：赚钱效应在扩散，优先盯主流、龙头和分歧后回流，不做无辨识度的杂毛。"
        playbook = [
            "优先主流热点里的龙头和容量中军。",
            "一致性太强时不追最后一脚，耐心等分歧后的承接回流。",
        ]
        warning = "高位一致后容易突然分歧，追涨前先看回封和承接。"
    elif score >= 1:
        label = "轮动平衡"
        tone = "neutral"
        cycle = "平衡轮动期"
        action = "养家视角：情绪不差，但还没到闭眼跟，只做有结构、有承接、能看清主次的前排。"
        playbook = [
            "先挑有结构的前排，再看是否有承接和回流。",
            "主流没完全打出来前，试错仓优先，别平均撒网。",
        ]
        warning = "轮动阶段后排掉队很快，不要把板块里所有票都当机会。"
    else:
        label = "情绪偏弱"
        tone = "caution"
        cycle = "退潮防守期"
        action = "养家视角：先看风险收益比，市场没有明显赚钱效应时，宁可少做，只盯恐慌后最先回流的方向。"
        playbook = [
            "强势股补跌未结束前，轻仓或空仓都算主动。",
            "如果没有新的主流故事，别把反抽错当成新周期。",
        ]
        warning = "高标补跌和跟风股失速往往同时出现，控制回撤比找机会更重要。"

    temperature = max(12, min(92, 52 + score * 10))

    return {
        "label": label,
        "tone": tone,
        "cycle": cycle,
        "temperature": temperature,
        "summary": f"涨停 {limit_up} 只，高涨幅个股 {rise} 只，活跃成交股 {active} 只，跌停 {limit_down} 只，下跌承压股 {pressure} 只。",
        "basis": [
            f"涨停强度：{limit_up} 只",
            f"高涨幅个股：{rise} 只",
            f"活跃成交股：{active} 只",
            f"跌停压力：{limit_down} 只",
            f"下跌承压股：{pressure} 只",
        ],
        "action": action,
        "playbook": playbook,
        "warning": warning,
        "score": score,
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


def _candidate_emotion(stock: dict[str, Any], row: dict[str, Any], theme_context: dict[str, Any]) -> dict[str, Any]:
    industry = _flatten(stock.get("industry") or "").strip() or "行业待定"
    group = (theme_context.get("groups_by_industry") or {}).get(industry)
    if not group:
        return {
            "score": 34,
            "label": "非主流",
            "tone": "caution",
            "summary": f"{industry}暂未进入当前样本里的热点前排，更适合补充观察，不适合先给高权重。",
        }

    tier_label = group.get("tier_label") or "轮动观察"
    tone = group.get("tone") or "neutral"
    if tier_label == "主流热点":
        score = 78
    elif tier_label == "次主流":
        score = 62
    else:
        score = 48
    return {
        "score": score,
        "label": tier_label,
        "tone": tone,
        "summary": (
            f"{industry}样本 {group.get('sample_count', 0)} 只，平均涨幅 {group.get('avg_change_pct', 0):.2f}% ，"
            f"活跃承接 {group.get('active_count', 0)} 只。"
        ),
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


def _candidate_leader(stock: dict[str, Any], row: dict[str, Any], theme_context: dict[str, Any]) -> dict[str, Any]:
    industry = _flatten(stock.get("industry") or "").strip() or "行业待定"
    group = (theme_context.get("groups_by_industry") or {}).get(industry)
    if not group:
        return {
            "score": 28,
            "label": "非核心观察",
            "tone": "caution",
            "summary": f"{industry}当前不在热点前排，先别把它当成龙头或核心容量来处理。",
        }

    stock_key = (
        _flatten(stock.get("ts_code") or "").strip()
        or _flatten(stock.get("symbol") or "").strip()
        or _flatten(stock.get("name") or "").strip()
    )
    role = (group.get("roles") or {}).get(stock_key)
    if role:
        return role

    return {
        "score": 48 if group.get("tier_label") != "非主流" else 30,
        "label": "跟风观察",
        "tone": "neutral" if group.get("tier_label") != "非主流" else "caution",
        "summary": f"{industry}有热点样本，但这只票更像跟随股，适合看承接，不适合先给龙头溢价。",
    }


def _candidate_overall(
    structure: dict[str, Any],
    emotion: dict[str, Any],
    capacity: dict[str, Any],
    leader: dict[str, Any],
    stage: dict[str, Any],
) -> dict[str, Any]:
    score = round(
        structure.get("score", 0) * 0.42
        + emotion.get("score", 0) * 0.22
        + capacity.get("score", 0) * 0.18
        + leader.get("score", 0) * 0.18
    )
    if stage.get("tone") == "caution":
        score -= 8
    elif stage.get("tone") == "positive" and emotion.get("tone") == "positive":
        score += 4
    if structure.get("tone") == "caution":
        label = "暂不参与"
        tone = "caution"
        decision = "结构没站稳时，不把主流热度和龙头标签当买入理由。"
    elif score >= 74 and emotion.get("label") == "主流热点" and leader.get("tone") != "caution":
        label = "重点观察"
        tone = "positive"
        decision = "结构、主流梯队和龙头角色有一定共振，可以进重点观察池，但仍要等确认。"
    elif score >= 58:
        label = "候选观察"
        tone = "neutral"
        decision = "有一定可看点，适合列入候选池，等结构确认、主流强化或龙头回流。"
    else:
        label = "暂不参与"
        tone = "caution"
        decision = "强度不够整齐，先观察，不急着把它升级成交易对象。"
    return {"score": score, "label": label, "tone": tone, "decision": decision}


def _build_execution_loop(
    stock: dict[str, Any],
    analysis: dict[str, Any],
    profile_payload: dict[str, Any],
    stage: dict[str, Any],
    emotion: dict[str, Any],
    leader: dict[str, Any],
    capacity: dict[str, Any],
    quote_row: dict[str, Any],
) -> dict[str, Any]:
    plan = _execution_plan(stock, analysis, profile_payload, stage, emotion, leader, capacity, quote_row)
    discipline = _discipline_engine(analysis, stage, emotion, leader, capacity, quote_row, plan)
    review = _review_system(analysis, stage, emotion, leader)
    return {"plan": plan, "discipline": discipline, "review": review}


def _execution_plan(
    stock: dict[str, Any],
    analysis: dict[str, Any],
    profile_payload: dict[str, Any],
    stage: dict[str, Any],
    emotion: dict[str, Any],
    leader: dict[str, Any],
    capacity: dict[str, Any],
    quote_row: dict[str, Any],
) -> dict[str, Any]:
    trend = analysis.get("trend") or {}
    signals = analysis.get("signals") or []
    signal = _latest_signal(signals)
    risk_cards = analysis.get("risk_cards") or []
    risk_card = _latest_risk_card(risk_cards, signal)
    signal_text = f"{_signal_short_label(signal)} {signal.get('status_label') or ''}".strip() if signal else "暂无买卖点"
    invalidation = signal.get("invalidation_price") if signal else None
    quote_change = _parse_numeric(_row_value(quote_row, ["涨跌幅"]))

    if signal and signal.get("side") == "buy" and signal.get("status") == "confirmed" and emotion.get("label") == "主流热点":
        setup = "主流确认型"
        tone = "positive"
        verdict = "可以按计划跟踪"
        action = "先等分歧承接或回踩不破失效价，再考虑执行；确认买点不是追涨许可证。"
        position_hint = "半仓以下，必须带失效价。"
    elif signal and signal.get("side") == "buy" and signal.get("status") == "candidate":
        setup = "主流试错型" if emotion.get("label") in {"主流热点", "次主流"} else "结构观察型"
        tone = "neutral"
        verdict = "候选观察"
        action = "现在更适合挂进观察计划，等候选买点转确认，或者板块回流后再升级。"
        position_hint = "试错仓，确认前不加仓。"
    elif signal and signal.get("side") == "sell":
        setup = "风险回避型"
        tone = "caution"
        verdict = "暂不执行"
        action = "最后信号在卖方，先把反抽当成观察，而不是提前预设新一轮上攻。"
        position_hint = "不参与，除非后续结构重新修复。"
    else:
        setup = "等待确认型"
        tone = "neutral"
        verdict = "先排计划，不急执行"
        action = "没有清晰触发器时，计划先写清楚，执行上宁愿慢半拍，也不要乱出手。"
        position_hint = "观察仓或空仓更合适。"

    if stage.get("tone") == "caution" and tone != "caution":
        verdict = "轻仓观察"
        tone = "neutral"
        action = "市场处在防守期时，即便个股结构不差，也只配观察计划，不配主动作战。"
        position_hint = "轻仓试错或空仓等待。"

    if quote_change >= 7 and tone == "positive":
        action = f"{action} 当前涨幅 {quote_change:.2f}% 偏大，更适合等分歧，而不是直接追最后一脚。"

    basis = [
        f"市场阶段：{stage.get('label') or '未判断'} · {stage.get('cycle') or '阶段未明'}",
        f"主流梯队：{emotion.get('label') or '未归类'}",
        f"龙头角色：{leader.get('label') or '待判断'}",
        f"结构状态：{trend.get('label') or '结构不足'} · {signal_text}",
    ]
    if capacity.get("label"):
        basis.append(f"容量情况：{capacity.get('label')} · {capacity.get('summary') or ''}".strip())
    if invalidation is not None:
        basis.append(f"失效价：{_price_text(invalidation)}")

    avoid_if = [
        "热点梯队掉队，龙头和前排失去承接。",
        "结构重新跌回中枢内部，或者买点失效。",
        "市场情绪从主流活跃切回退潮防守期。",
    ]
    if risk_card and risk_card.get("discipline"):
        avoid_if.insert(0, risk_card.get("discipline"))

    return {
        "title": "交易计划",
        "tone": tone,
        "setup": setup,
        "verdict": verdict,
        "summary": f"{setup}：{stock.get('name') or ''} 当前以 {emotion.get('label') or '观察'} + {leader.get('label') or '普通样本'} 的姿态进入执行观察。",
        "action": action,
        "position_hint": position_hint,
        "invalidation_price": invalidation,
        "basis": basis,
        "avoid_if": avoid_if,
        "watch_points": [
            "先看主流热度能不能继续扩散，再看个股承接。",
            "先看确认，再谈加仓；先看失效，再谈格局。",
            profile_payload.get("decision") or "综合交易画像只做辅助，不替代执行纪律。",
        ],
    }


def _discipline_engine(
    analysis: dict[str, Any],
    stage: dict[str, Any],
    emotion: dict[str, Any],
    leader: dict[str, Any],
    capacity: dict[str, Any],
    quote_row: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    trend = analysis.get("trend") or {}
    signal = _latest_signal(analysis.get("signals") or [])
    quote_change = _parse_numeric(_row_value(quote_row, ["涨跌幅"]))
    signal_summary = f"{_signal_short_label(signal)} {signal.get('status_label') or ''}".strip() if signal else "暂无买点"

    checks = [
        {
            "label": "主流是否支持",
            "passed": emotion.get("label") in {"主流热点", "次主流"},
            "detail": f"当前归类为 {emotion.get('label') or '未归类'}。",
        },
        {
            "label": "龙头辨识是否清楚",
            "passed": leader.get("label") in {"龙头候选", "容量中军", "前排助攻"},
            "detail": f"当前角色 {leader.get('label') or '待判断'}。",
        },
        {
            "label": "结构是否允许执行",
            "passed": bool(signal) and signal.get("side") == "buy" and signal.get("status") != "invalid" and trend.get("direction") != "down",
            "detail": f"当前信号 {signal_summary}。",
        },
        {
            "label": "风报比是否明确",
            "passed": signal is not None and signal.get("invalidation_price") is not None,
            "detail": "有失效价，才能谈纪律，不然只是模糊看多。",
        },
        {
            "label": "是否避免冲动追涨",
            "passed": quote_change <= 7,
            "detail": f"当前涨跌幅 {quote_change:.2f}% 。",
        },
        {
            "label": "市场阶段是否允许放大仓位",
            "passed": stage.get("tone") != "caution" and capacity.get("label") != "容量待核",
            "detail": f"市场 {stage.get('label') or '未判断'}，容量 {capacity.get('label') or '待判断'}。",
        },
    ]

    score = round(sum(1 for item in checks if item["passed"]) / max(len(checks), 1) * 100)
    if score >= 84:
        label = "合规执行"
        tone = "positive"
        summary = "这笔计划大体符合主流、结构、仓位三条线，可以进执行观察。"
        next_step = "先按计划等确认或分歧承接，不需要临盘临时改剧本。"
    elif score >= 60:
        label = "轻仓试错"
        tone = "neutral"
        summary = "有些条件对了，但还没到可以放大仓位的时候，更像试错而不是主攻。"
        next_step = "如果后续主流和结构继续共振，再把它从观察升级到执行。"
    else:
        label = "纪律优先"
        tone = "caution"
        summary = "现在更该尊重纪律，先把不清楚的点看清，再决定要不要参与。"
        next_step = "宁可错过，不要在看不清主流、结构或失效价时强行出手。"

    return {
        "title": "纪律引擎",
        "tone": tone,
        "score": score,
        "label": label,
        "summary": summary,
        "next_step": next_step,
        "checks": checks,
        "position_hint": plan.get("position_hint") or "先看计划再谈仓位。",
    }


def _review_system(
    analysis: dict[str, Any],
    stage: dict[str, Any],
    emotion: dict[str, Any],
    leader: dict[str, Any],
) -> dict[str, Any]:
    backtest = analysis.get("backtest") or {}
    summary = backtest.get("summary") or {}
    trades = backtest.get("trades") or []
    observed = [item for item in trades if item.get("bars", 0) > 0]
    recent_cases = observed[-4:]
    avg_forward = float(summary.get("avg_favorable_pct") or 0)
    avg_adverse = float(summary.get("avg_adverse_pct") or 0)

    if not observed:
        tone = "neutral"
        label = "样本不足"
        text = "当前级别的历史信号样本还不够，复盘结论先以观察为主。"
    elif avg_forward >= avg_adverse and summary.get("invalid", 0) <= max(1, summary.get("observed", 0) // 3):
        tone = "positive"
        label = "顺向占优"
        text = "过去这组信号整体顺向空间更大，说明结构一旦做对，推进效率还可以。"
    elif avg_adverse > avg_forward:
        tone = "caution"
        label = "逆向偏多"
        text = "历史样本里的逆向压力更大，先把风控和等待确认放在收益想象前面。"
    else:
        tone = "neutral"
        label = "震荡观察"
        text = "历史样本有来有回，执行上更适合先轻仓，再根据承接反馈决定是否升级。"

    lessons = [
        f"历史信号 {summary.get('signals', 0)} 次，已进入观察窗口 {summary.get('observed', 0)} 次。",
        f"平均顺向空间 {avg_forward * 100:.2f}% ，平均逆向压力 {avg_adverse * 100:.2f}%。",
        f"当前市场阶段 {stage.get('cycle') or '未明'}，热点归类 {emotion.get('label') or '未归类'}，角色 {leader.get('label') or '待判断'}。",
    ]
    if summary.get("invalid", 0):
        lessons.append(f"结构失效样本 {summary.get('invalid', 0)} 次，说明失效价必须当真。")

    cases = []
    for item in recent_cases:
        cases.append(
            {
                "label": item.get("label") or "",
                "date": item.get("date") or "",
                "outcome": item.get("outcome") or "待观察",
                "forward_pct": round(float(item.get("max_favorable_pct") or 0) * 100, 2),
                "adverse_pct": round(float(item.get("max_adverse_pct") or 0) * 100, 2),
                "close_return_pct": round(float(item.get("close_return_pct") or 0) * 100, 2),
            }
        )

    return {
        "title": "复盘系统",
        "tone": tone,
        "label": label,
        "summary": text,
        "lessons": lessons,
        "recent_cases": cases,
        "note": backtest.get("note") or "复盘统计只用于训练风报比感知，不替代盘中执行。",
    }


def _theme_member_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": item.get("symbol", ""),
        "ts_code": item.get("ts_code", ""),
        "name": item.get("name", ""),
        "change_pct": item.get("change_pct", ""),
        "amount": item.get("amount", ""),
        "turnover": item.get("turnover", ""),
    }


def _match_market_row(stock: dict[str, Any], market_cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    code = _flatten(stock.get("symbol") or "").strip().upper()
    ts_code = _flatten(stock.get("ts_code") or "").split(".")[0].strip().upper()
    name = _flatten(stock.get("name") or "").strip()
    for card in market_cards:
        for row in card.get("sample_rows", []) or []:
            row_code = _row_value(row, ["股票代码", "代码"]).strip().upper()
            row_name = _row_value(row, ["股票简称", "股票名称", "名称"]).strip()
            if row_code and row_code in {code, ts_code}:
                return row
            if row_name and row_name == name:
                return row
    return None


def _row_value(row: dict[str, Any], keywords: list[str]) -> str:
    if not isinstance(row, dict):
        return ""
    for key, value in row.items():
        key_text = _flatten(key)
        if any(keyword in key_text for keyword in keywords):
            return _flatten(value)
    return ""


def _parse_watchlist_targets(text: str) -> list[str]:
    parts = re.split(r"[\n\r,，;；]+", str(text or ""))
    targets: list[str] = []
    seen: set[str] = set()
    for part in parts:
        target = _normalize_watchlist_target(part)
        if not target:
            continue
        key = target.upper()
        if key in seen:
            continue
        seen.add(key)
        targets.append(target)
    return targets


def _normalize_watchlist_target(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip(" -\t")
    if not cleaned:
        return ""
    ts_code_match = re.search(r"\b(\d{6}\.(?:SH|SZ|BJ))\b", cleaned, re.IGNORECASE)
    if ts_code_match:
        return ts_code_match.group(1).upper()
    symbol_match = re.search(r"\b(\d{6})\b", cleaned)
    if symbol_match:
        return symbol_match.group(1)
    return cleaned


def _mx_manage_succeeded(result: dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    return result.get("status") in (0, "0", None) or result.get("code") in (0, "0", None)


def _mx_manage_success_text(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "操作成功"
    return _flatten(result.get("data") or result.get("message") or "操作成功")


def _mx_manage_result_text(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "返回格式异常"
    parts = [
        f"message={_flatten(result.get('message') or '') or '-'}",
        f"status={_flatten(result.get('status') or '') or '-'}",
        f"code={_flatten(result.get('code') or '') or '-'}",
    ]
    data_text = _flatten(result.get("data") or "")
    if data_text:
        parts.append(f"data={data_text}")
    return "，".join(parts)


def _mx_manage_group_confirmed(result: dict[str, Any], group_name: str) -> bool:
    text = " ".join(
        [
            _flatten((result or {}).get("message") or ""),
            _flatten((result or {}).get("data") or ""),
        ]
    )
    return bool(group_name and group_name in text) or "分组" in text or "自选股组" in text


def _eastmoney_header_dict(raw: str) -> dict[str, str]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return {str(key).strip(): str(value).strip() for key, value in parsed.items() if str(key).strip() and str(value).strip()}
    except json.JSONDecodeError:
        pass
    headers: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            headers[key] = value
    return headers


def _parse_eastmoney_jsonp(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    match = re.search(r"\((.*)\)\s*;?\s*$", text, flags=re.S)
    if not match:
        raise MXProviderError("东方财富分组返回内容不是 JSONP。", 502)
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise MXProviderError("东方财富分组返回内容无法解析。", 502) from exc
    if not isinstance(payload, dict):
        raise MXProviderError("东方财富分组返回格式异常。", 502)
    return payload


def _eastmoney_find_group_id(groups: list[dict[str, Any]], group_name: str) -> str:
    for group in groups or []:
        name = _flatten(group.get("gname") or group.get("name") or "")
        if name == group_name:
            return _flatten(group.get("gid") or group.get("id") or "")
    return ""


def _eastmoney_stock_code(target: str) -> str:
    text = _flatten(target).strip().upper()
    symbol = text.split(".", 1)[0]
    if not re.fullmatch(r"\d{6}", symbol):
        raise MXProviderError("东方财富分组直连只支持 6 位 A 股代码。", 400)
    market = "1" if symbol.startswith(("5", "6", "9")) else "0"
    return f"{market}${symbol}"


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


def _board_source_label(source: str) -> str:
    mapping = {
        "dc": "东方财富",
        "tdx": "通达信",
        "ths": "同花顺",
    }
    return mapping.get(_flatten(source).strip().lower(), "板块")
