from __future__ import annotations

from typing import Any

from .chanlun import analyze_klines
from .config import LEVELS, default_date_range, normalize_yyyymmdd
from .data_provider import DataProviderError, TushareClient


def create_app(data_client: TushareClient | None = None):
    from pathlib import Path

    from flask import Flask, jsonify, render_template, request

    app = Flask(__name__)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    client = data_client or TushareClient()

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
            result["stock"] = stock.as_dict()
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
