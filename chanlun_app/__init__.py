from __future__ import annotations

from typing import Any

from .ai_profile import AIProviderError, ClaudeProfileExplainer
from .chanlun import analyze_klines
from .config import LEVELS, default_date_range, normalize_yyyymmdd
from .data_provider import DataProviderError, TushareClient
from .mx_provider import MXDataProvider, MXProviderError
from .review_service import ReviewService
from .smart_picker import SmartPickerService
from .system_config_store import SystemConfigStore, SystemConfigStoreError, mysql_dsn_from_env
from .theme_board_service import ThemeBoardService
from .theme_research_service import ThemeResearchError, ThemeResearchService
from .trading_profile import TradingProfileService
from .watchtower_service import WatchtowerService

TRADING_PROFILE_EXTERNAL_TIMEOUT_SECONDS = 3
TRADING_PROFILE_AI_TIMEOUT_SECONDS = 35
REVIEW_AI_TIMEOUT_SECONDS = 45


def create_app(
    data_client: TushareClient | None = None,
    mx_client: MXDataProvider | None = None,
    profile_client: TradingProfileService | None = None,
    picker_client: SmartPickerService | None = None,
    ai_client: ClaudeProfileExplainer | None = None,
    review_client: ReviewService | None = None,
    watchtower_client: WatchtowerService | None = None,
    theme_board_client: ThemeBoardService | None = None,
    theme_research_client: ThemeResearchService | None = None,
    system_config_client: SystemConfigStore | None = None,
):
    from pathlib import Path

    from flask import Flask, Response, jsonify, render_template, request, stream_with_context

    app = Flask(__name__)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    client = data_client or TushareClient()
    mx_provider = mx_client or MXDataProvider(timeout_seconds=TRADING_PROFILE_EXTERNAL_TIMEOUT_SECONDS)
    ai_explainer = ai_client or ClaudeProfileExplainer(timeout_seconds=TRADING_PROFILE_AI_TIMEOUT_SECONDS)
    trading_profile = profile_client or TradingProfileService(mx_data_provider=mx_provider, ai_explainer=ai_explainer)
    smart_picker = picker_client or SmartPickerService(
        data_client=client,
        mx_data_provider=mx_provider,
        trading_profile=trading_profile,
    )
    review_service = review_client or ReviewService(
        data_client=client,
        ai_explainer=ClaudeProfileExplainer(timeout_seconds=REVIEW_AI_TIMEOUT_SECONDS),
    )
    watchtower_service = watchtower_client or WatchtowerService(
        data_client=client,
        picker_client=smart_picker,
    )
    theme_board_service = theme_board_client or ThemeBoardService(data_client=client)
    theme_research_service = theme_research_client or ThemeResearchService(dsn=mysql_dsn_from_env())
    system_config_store = system_config_client or SystemConfigStore(dsn=mysql_dsn_from_env())

    def json_error(message: str, status_code: int):
        return jsonify({"error": {"message": message, "status_code": status_code}}), status_code

    @app.get("/")
    def index():
        static_dir = Path(app.static_folder or "")
        version = max(
            (static_dir / "app.js").stat().st_mtime,
            (static_dir / "styles.css").stat().st_mtime,
        )
        return render_template("index.html", levels=LEVELS, static_version=int(version))

    @app.get("/api/stocks/search")
    def search_stocks():
        query = request.args.get("q", "")
        limit = _safe_int(request.args.get("limit"), 20, 1, 50)
        try:
            return jsonify({"items": client.search_stocks(query, limit=limit)})
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/boards/search")
    def search_boards():
        query = request.args.get("q", "")
        board_type = request.args.get("type", "")
        source = request.args.get("source", "dc")
        limit = _safe_int(request.args.get("limit"), 12, 1, 50)
        try:
            return jsonify({"items": client.search_boards(source=source, query=query, board_type=board_type, limit=limit)})
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/analysis")
    def analysis():
        query = request.args.get("ts_code") or request.args.get("q") or ""
        level = request.args.get("level", "daily")
        if level not in LEVELS:
            return json_error(f"level 只支持 {'、'.join(LEVELS)}。", 400)

        default_start, default_end = default_date_range(level)
        start_date = normalize_yyyymmdd(request.args.get("start_date")) or default_start
        end_date = normalize_yyyymmdd(request.args.get("end_date")) or default_end

        try:
            stock = client.resolve_stock(query)
            stock_payload = stock.as_dict()
            try:
                stock_payload["dc_concepts"] = client.get_stock_dc_concepts(stock.ts_code)
            except DataProviderError:
                stock_payload["dc_concepts"] = []
            try:
                stock_payload["bak_basic"] = client.get_stock_bak_basic(stock.ts_code)
            except DataProviderError:
                stock_payload["bak_basic"] = {}
            context_items = []
            for context_level in _higher_context_levels(level):
                context_start, _context_end = default_date_range(context_level)
                try:
                    context_klines = client.get_klines(stock.ts_code, context_level, context_start, end_date)
                    context_result = analyze_klines(context_klines, level=context_level)
                    context_items.append(_level_summary(context_level, context_result))
                except DataProviderError as exc:
                    context_items.append(
                        {
                            "level": context_level,
                            "label": LEVELS[context_level]["label"],
                            "status": "error",
                            "error": exc.message,
                        }
                    )

            klines = client.get_klines(stock.ts_code, level, start_date, end_date)
            result = analyze_klines(klines, level=level)
            result["stock"] = stock_payload
            result["query"] = {
                "level": level,
                "level_label": LEVELS[level]["label"],
                "start_date": start_date,
                "end_date": end_date,
            }
            result["level_context"] = {
                "primary_level": level,
                "items": context_items + [_level_summary(level, result)],
            }
            return jsonify(result)
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/mx/summary")
    def mx_summary():
        ts_code = (request.args.get("ts_code") or "").strip()
        name = (request.args.get("name") or "").strip()
        if not ts_code and not name:
            return json_error("请输入股票名称或代码。", 400)

        try:
            return jsonify(mx_provider.summary(ts_code=ts_code, name=name))
        except MXProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/mx/news")
    def mx_news():
        ts_code = (request.args.get("ts_code") or "").strip()
        name = (request.args.get("name") or "").strip()
        target = name or ts_code
        if not target:
            return json_error("请输入股票名称或代码。", 400)

        try:
            return jsonify(trading_profile.news_provider.digest(target=target))
        except MXProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/trading-profile")
    def profile_summary():
        payload = request.get_json(silent=True) or {}
        stock = payload.get("stock") or {}
        analysis = payload.get("analysis") or {}
        include_mx_summary = payload.get("include_mx_summary", True)
        include_ai_summary = payload.get("include_ai_summary", True)
        if not stock:
            return json_error("缺少股票信息，无法生成交易画像。", 400)

        try:
            build_with_options = getattr(trading_profile, "build_with_options", None)
            if callable(build_with_options):
                payload = build_with_options(
                    stock=stock,
                    analysis=analysis,
                    include_mx_summary=bool(include_mx_summary),
                    include_ai_summary=bool(include_ai_summary),
                )
            else:
                payload = trading_profile.build(
                    stock=stock,
                    analysis=analysis,
                    include_mx_summary=bool(include_mx_summary),
                )
            return jsonify(
                payload
            )
        except MXProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/analysis/watchlist")
    def analysis_watchlist_manage():
        payload = request.get_json(silent=True) or {}
        action = str(payload.get("action", "add") or "add").strip().lower()
        stock = payload.get("stock") or {}
        bak_basic = payload.get("bak_basic") or stock.get("bak_basic") or {}
        target = (
            str(stock.get("ts_code") or "").strip()
            or str(stock.get("symbol") or "").strip()
            or str(stock.get("name") or "").strip()
        )
        if not target:
            return json_error("缺少股票信息，无法加入自选。", 400)

        try:
            watchlist_result = smart_picker.manage_watchlist(action=action, target=target)
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

        cache_result: dict[str, Any]
        try:
            cache_result = client.save_stock_basic_cache(stock=stock, bak_basic=bak_basic)
        except DataProviderError as exc:
            cache_result = {"status": "error", "message": exc.message}

        watchtower_result: dict[str, Any]
        try:
            if action == "delete":
                deleted = watchtower_service.store.delete_entry(str(stock.get("ts_code") or target).strip().upper())
                watchtower_result = {"status": "ok", "deleted": deleted}
            else:
                watchtower_result = watchtower_service.track_stock(stock=stock, bak_basic=bak_basic)
        except DataProviderError as exc:
            watchtower_result = {"status": "error", "message": exc.message}

        return jsonify(
            {
                **watchlist_result,
                "stock": {
                    "ts_code": stock.get("ts_code", ""),
                    "symbol": stock.get("symbol", ""),
                    "name": stock.get("name", ""),
                },
                "cache": cache_result,
                "watchtower": watchtower_result,
            }
        )

    @app.get("/api/smart-picker/overview")
    def smart_picker_overview():
        try:
            return jsonify(smart_picker.overview())
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/smart-picker/screen")
    def smart_picker_screen():
        payload = request.get_json(silent=True) or {}
        level = payload.get("level", "daily")
        limit = _safe_int(payload.get("limit"), 20, 1, 300)
        source_type = str(payload.get("source_type", "")).strip().lower()
        query_text = payload.get("query_text", "")
        screen_filters = {
            "technical_shape": payload.get("technical_shape", ""),
            "market_scope": payload.get("market_scope", ""),
            "turnover_min": payload.get("turnover_min", ""),
            "turnover_max": payload.get("turnover_max", ""),
            "market_cap_min": payload.get("market_cap_min", ""),
            "market_cap_max": payload.get("market_cap_max", ""),
        }
        board_filters = [
            {
                "source": "dc",
                "ts_code": payload.get("board_ts_code", ""),
                "name": payload.get("board_name", ""),
                "board_type": payload.get("board_type", ""),
            },
            {
                "source": "tdx",
                "ts_code": payload.get("tdx_board_ts_code", ""),
                "name": payload.get("tdx_board_name", ""),
                "board_type": payload.get("tdx_board_type", ""),
            },
            {
                "source": "ths",
                "ts_code": payload.get("ths_board_ts_code", ""),
                "name": payload.get("ths_board_name", ""),
                "board_type": payload.get("ths_board_type", ""),
            },
        ]
        try:
            if source_type == "watchlist":
                watchlist_limit = None if payload.get("limit_all", False) else limit
                return jsonify(smart_picker.screen_watchlist(level=level, limit=watchlist_limit, screen_filters=screen_filters))
            return jsonify(
                smart_picker.screen_with_scopes(
                    query_text=query_text,
                    level=level,
                    limit=limit,
                    board_filters=board_filters,
                    screen_filters=screen_filters,
                )
            )
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/smart-picker/candidate")
    def smart_picker_candidate():
        payload = request.get_json(silent=True) or {}
        stock = payload.get("stock") or {}
        level = payload.get("level", "daily")
        try:
            return jsonify(smart_picker.candidate_detail(stock=stock, level=level))
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/smart-picker/watchlist")
    def smart_picker_watchlist():
        try:
            return jsonify(smart_picker.watchlist())
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/smart-picker/watchlist")
    def smart_picker_watchlist_manage():
        payload = request.get_json(silent=True) or {}
        action = payload.get("action", "")
        target = payload.get("target", "")
        try:
            return jsonify(smart_picker.manage_watchlist(action=action, target=target))
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/smart-picker/eastmoney-batch")
    def smart_picker_eastmoney_batch():
        payload = request.get_json(silent=True) or {}
        action = payload.get("action", "")
        group_name = payload.get("group_name", "")
        targets_text = payload.get("targets_text", "")
        try:
            return jsonify(
                smart_picker.batch_manage_watchlist(
                    action=action,
                    group_name=group_name,
                    targets_text=targets_text,
                )
            )
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/smart-picker/ai-brief")
    def smart_picker_ai_brief():
        payload = request.get_json(silent=True) or {}
        stock = payload.get("stock") or {}
        analysis = payload.get("analysis") or {}
        profile = payload.get("profile") or {}
        if not stock:
            return json_error("缺少股票信息，无法生成 AI 解读。", 400)
        if not profile:
            return json_error("缺少交易画像事实层，无法生成 AI 解读。", 400)
        try:
            return jsonify(ai_explainer.explain(stock=stock, analysis=analysis, profile_payload=profile))
        except AIProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/review/overview")
    def review_overview():
        trade_date = normalize_yyyymmdd(request.args.get("trade_date"))
        try:
            return jsonify(review_service.overview(trade_date=trade_date))
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/review/ai-brief")
    def review_ai_brief():
        payload = request.get_json(silent=True) or {}
        review_payload = payload.get("review") or {}
        if not review_payload:
            return json_error("缺少复盘事实层数据，无法生成 AI 复盘结论。", 400)
        try:
            return jsonify(review_service.explain_overview(review_payload))
        except AIProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/watchtower/overview")
    def watchtower_overview():
        query = request.args.get("q", "")
        page = _safe_int(request.args.get("page"), 1, 1, 9999)
        page_size = _safe_int(request.args.get("page_size"), 12, 1, 50)
        try:
            return jsonify(watchtower_service.overview(query=query, page=page, page_size=page_size))
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/watchtower/delete")
    def watchtower_delete():
        payload = request.get_json(silent=True) or {}
        ts_code = str(payload.get("ts_code") or "").strip()
        try:
            return jsonify(watchtower_service.delete_stock(ts_code))
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/watchtower/eastmoney-add")
    def watchtower_eastmoney_add():
        payload = request.get_json(silent=True) or {}
        ts_code = str(payload.get("ts_code") or "").strip()
        try:
            return jsonify(watchtower_service.add_to_eastmoney_group(ts_code))
        except (DataProviderError, MXProviderError) as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/watchtower/realtime")
    def watchtower_realtime():
        ts_code = str(request.args.get("ts_code") or "").strip()
        try:
            return jsonify(watchtower_service.realtime_detail(ts_code))
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/theme-board/overview")
    def theme_board_overview():
        trade_date = normalize_yyyymmdd(request.args.get("trade_date"))
        try:
            return jsonify(theme_board_service.overview(trade_date=trade_date))
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/theme-board/detail")
    def theme_board_detail():
        trade_date = normalize_yyyymmdd(request.args.get("trade_date"))
        ts_code = str(request.args.get("ts_code") or "").strip()
        name = str(request.args.get("name") or "").strip()
        if not ts_code and not name:
            return json_error("请输入题材代码或题材名称。", 400)
        try:
            return jsonify(theme_board_service.detail(trade_date=trade_date, ts_code=ts_code, name=name))
        except DataProviderError as exc:
            return json_error(exc.message, exc.status_code)

    @app.post("/api/theme-research/start")
    def theme_research_start():
        payload = request.get_json(silent=True) or {}
        theme_name = str(payload.get("theme_name") or "").strip()
        market = str(payload.get("market") or "A股").strip() or "A股"
        analysis_depth = str(payload.get("analysis_depth") or "standard").strip() or "standard"
        time_horizon = str(payload.get("time_horizon") or "短中线").strip() or "短中线"
        if not theme_name:
            return json_error("请输入行业、题材或概念名称。", 400)
        try:
            return jsonify(
                theme_research_service.start_task(
                    theme_name=theme_name,
                    market=market,
                    analysis_depth=analysis_depth,
                    time_horizon=time_horizon,
                )
            )
        except ThemeResearchError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/theme-research/stream/<task_id>")
    def theme_research_stream(task_id: str):
        try:
            stream = theme_research_service.event_stream(str(task_id or "").strip())
        except ThemeResearchError as exc:
            return json_error(exc.message, exc.status_code)
        return Response(
            stream_with_context(stream),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/theme-research/report/<task_id>")
    def theme_research_report(task_id: str):
        try:
            return jsonify(theme_research_service.get_report(str(task_id or "").strip()))
        except ThemeResearchError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/theme-research/reports")
    def theme_research_reports():
        limit = _safe_int(request.args.get("limit"), 12, 1, 50)
        page = _safe_int(request.args.get("page"), 1, 1, 9999)
        page_size = _safe_int(request.args.get("page_size"), limit, 1, 50)
        try:
            return jsonify(theme_research_service.list_reports(limit=limit, page=page, page_size=page_size))
        except ThemeResearchError as exc:
            return json_error(exc.message, exc.status_code)

    @app.get("/api/system-configs")
    def system_config_list():
        try:
            return jsonify(
                {
                    "enabled": system_config_store.enabled,
                    "items": system_config_store.list_entries(),
                }
            )
        except SystemConfigStoreError as exc:
            return json_error(str(exc), 500)

    @app.get("/api/system-configs/<config_key>")
    def system_config_detail(config_key: str):
        try:
            item = system_config_store.get_entry(config_key)
        except SystemConfigStoreError as exc:
            return json_error(str(exc), 500)
        if not item:
            return json_error("未找到对应系统配置。", 404)
        return jsonify({"item": item})

    @app.post("/api/system-configs")
    def system_config_upsert():
        payload = request.get_json(silent=True) or {}
        config_key = str(payload.get("config_key") or "").strip()
        if not config_key:
            return json_error("配置键不能为空。", 400)
        try:
            item = system_config_store.upsert_entry(
                config_key=config_key,
                config_value=str(payload.get("config_value") or ""),
                label=str(payload.get("label") or ""),
                category=str(payload.get("category") or ""),
                description=str(payload.get("description") or ""),
                is_secret=bool(payload.get("is_secret", True)),
                is_enabled=bool(payload.get("is_enabled", True)),
            )
            return jsonify({"status": "ok", "item": item})
        except SystemConfigStoreError as exc:
            return json_error(str(exc), 500)

    @app.delete("/api/system-configs/<config_key>")
    def system_config_delete(config_key: str):
        try:
            deleted = system_config_store.delete_entry(config_key)
        except SystemConfigStoreError as exc:
            return json_error(str(exc), 500)
        if not deleted:
            return json_error("未找到对应系统配置。", 404)
        return jsonify({"status": "ok", "deleted": True, "config_key": config_key.upper()})

    @app.errorhandler(404)
    def not_found(_exc):
        return json_error("接口不存在。", 404)

    return app


def _safe_int(value: str | None, default: int, lower: int, upper: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        parsed = default
    return max(lower, min(parsed, upper))


def _higher_context_levels(level: str) -> list[str]:
    if level in {"min30", "min60"}:
        return ["monthly", "weekly", "daily"]
    if level == "daily":
        return ["monthly", "weekly"]
    if level == "weekly":
        return ["monthly"]
    return []


def _level_summary(level: str, result: dict[str, Any]) -> dict[str, Any]:
    centers = result.get("centers") or []
    signals = result.get("signals") or []
    divergences = result.get("divergences") or []
    trend = result.get("trend") or {}
    last_center = centers[-1] if centers else None
    last_signal = signals[-1] if signals else None
    last_divergence = divergences[-1] if divergences else None
    counts = (result.get("meta") or {}).get("counts") or {}

    return {
        "level": level,
        "label": LEVELS[level]["label"],
        "status": "ok",
        "trend": trend,
        "counts": counts,
        "last_center": _compact_center(last_center),
        "last_signal": _compact_signal(last_signal),
        "last_divergence": _compact_divergence(last_divergence),
    }


def _compact_center(center: dict[str, Any] | None) -> dict[str, Any] | None:
    if not center:
        return None
    return {
        "id": center.get("id", ""),
        "start_date": center.get("start_date", ""),
        "end_date": center.get("end_date", ""),
        "low": center.get("low"),
        "high": center.get("high"),
        "status": center.get("status", ""),
        "status_label": center.get("status_label", ""),
        "breakout_direction": center.get("breakout_direction", ""),
        "reason": center.get("reason", ""),
    }


def _compact_signal(signal: dict[str, Any] | None) -> dict[str, Any] | None:
    if not signal:
        return None
    return {
        "id": signal.get("id", ""),
        "type": signal.get("type", ""),
        "side": signal.get("side", ""),
        "date": signal.get("date", ""),
        "price": signal.get("price"),
        "status": signal.get("status", ""),
        "status_label": signal.get("status_label", ""),
        "invalidation_price": signal.get("invalidation_price"),
    }


def _compact_divergence(divergence: dict[str, Any] | None) -> dict[str, Any] | None:
    if not divergence:
        return None
    return {
        "id": divergence.get("id", ""),
        "label": divergence.get("label", ""),
        "side": divergence.get("side", ""),
        "date": divergence.get("date", ""),
        "price": divergence.get("price"),
        "current_strength": divergence.get("current_strength"),
        "previous_strength": divergence.get("previous_strength"),
    }
