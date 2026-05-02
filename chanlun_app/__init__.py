from __future__ import annotations

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
            return json_error("level 只支持 daily、weekly、monthly。", 400)

        default_start, default_end = default_date_range(level)
        start_date = normalize_yyyymmdd(request.args.get("start_date")) or default_start
        end_date = normalize_yyyymmdd(request.args.get("end_date")) or default_end

        try:
            stock = client.resolve_stock(query)
            klines = client.get_klines(stock.ts_code, level, start_date, end_date)
            result = analyze_klines(klines, level=level)
            result["stock"] = stock.as_dict()
            result["query"] = {
                "level": level,
                "start_date": start_date,
                "end_date": end_date,
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
