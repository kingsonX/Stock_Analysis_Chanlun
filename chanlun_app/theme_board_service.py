from __future__ import annotations

from collections import defaultdict
from typing import Any

from .data_provider import DataProviderError, TushareClient


class ThemeBoardService:
    def __init__(self, data_client: TushareClient | None = None):
        self.data_client = data_client or TushareClient()

    def overview(self, trade_date: str | None = None) -> dict[str, Any]:
        concept_payload = self.data_client.get_kpl_concept_cons(trade_date=trade_date)
        kpl_list_items: list[dict[str, Any]] = []
        try:
            kpl_list_items = self.data_client.get_kpl_list(trade_date=concept_payload.get("trade_date") or trade_date).get("items", [])
        except DataProviderError:
            kpl_list_items = []

        items = _build_theme_rankings(concept_payload.get("items", []), kpl_list_items)
        unique_stocks = {
            str(item.get("con_code") or "").strip().upper()
            for item in concept_payload.get("items", [])
            if str(item.get("con_code") or "").strip()
        }
        summary = {
            "theme_count": len(items),
            "stock_count": len(unique_stocks),
            "leader_name": items[0]["name"] if items else "",
            "leader_stock_count": items[0]["stock_count"] if items else 0,
            "leader_hot_total": items[0]["hot_total"] if items else 0,
            "kpl_stock_count": len(kpl_list_items),
        }
        return {
            "status": "ok",
            "trade_date": concept_payload.get("trade_date") or trade_date or "",
            "summary": summary,
            "items": items,
        }

    def detail(self, trade_date: str | None = None, ts_code: str = "", name: str = "") -> dict[str, Any]:
        clean_ts_code = str(ts_code or "").strip().upper()
        clean_name = str(name or "").strip()
        payload = self.data_client.get_kpl_concept_cons(trade_date=trade_date, ts_code=clean_ts_code or None)
        items = payload.get("items", [])
        if clean_name:
            items = [item for item in items if str(item.get("name") or "").strip() == clean_name]
        if clean_ts_code:
            items = [item for item in items if str(item.get("ts_code") or "").strip().upper() == clean_ts_code]

        grouped = _build_theme_rankings(items, [])
        if not grouped:
            raise DataProviderError("没有获取到该题材的成分股数据，请检查交易日期或题材代码。", 404)
        theme = grouped[0]
        members = sorted(
            [
                {
                    "ts_code": str(item.get("con_code") or "").strip().upper(),
                    "name": str(item.get("con_name") or "").strip(),
                    "theme_ts_code": str(item.get("ts_code") or "").strip().upper(),
                    "theme_name": str(item.get("name") or "").strip(),
                    "trade_date": str(item.get("trade_date") or payload.get("trade_date") or "").strip(),
                    "hot_num": _to_int(item.get("hot_num")),
                    "desc": str(item.get("desc") or "").strip(),
                }
                for item in items
            ],
            key=lambda row: (row["hot_num"], row["name"]),
            reverse=True,
        )
        return {
            "status": "ok",
            "trade_date": payload.get("trade_date") or trade_date or "",
            "theme": theme,
            "items": members,
        }


def _build_theme_rankings(items: list[dict[str, Any]], kpl_list_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    board_hits = _build_kpl_theme_hits(kpl_list_items)
    grouped: dict[str, dict[str, Any]] = {}
    for item in items or []:
        theme_code = str(item.get("ts_code") or "").strip().upper()
        theme_name = str(item.get("name") or "").strip()
        if not theme_code and not theme_name:
            continue
        key = theme_code or theme_name
        group = grouped.setdefault(
            key,
            {
                "ts_code": theme_code,
                "name": theme_name,
                "trade_date": str(item.get("trade_date") or "").strip(),
                "stock_codes": set(),
                "stock_names": [],
                "hot_total": 0,
                "hot_max": 0,
                "descs": [],
                "leaders": [],
            },
        )
        stock_code = str(item.get("con_code") or "").strip().upper()
        stock_name = str(item.get("con_name") or "").strip()
        hot_num = _to_int(item.get("hot_num"))
        if stock_code:
            group["stock_codes"].add(stock_code)
        if stock_name and stock_name not in group["stock_names"]:
            group["stock_names"].append(stock_name)
        group["hot_total"] += hot_num
        group["hot_max"] = max(group["hot_max"], hot_num)
        desc = str(item.get("desc") or "").strip()
        if desc and desc not in group["descs"]:
            group["descs"].append(desc)
        if stock_name:
            group["leaders"].append({"name": stock_name, "ts_code": stock_code, "hot_num": hot_num})

    rows: list[dict[str, Any]] = []
    for group in grouped.values():
        leaders = sorted(group["leaders"], key=lambda row: (row["hot_num"], row["name"]), reverse=True)
        stock_count = len(group["stock_codes"])
        hot_total = int(group["hot_total"])
        row = {
            "ts_code": group["ts_code"],
            "name": group["name"],
            "trade_date": group["trade_date"],
            "stock_count": stock_count,
            "hot_total": hot_total,
            "hot_avg": round(hot_total / stock_count, 2) if stock_count else 0,
            "hot_max": group["hot_max"],
            "top_stock": leaders[0] if leaders else {},
            "stock_names": group["stock_names"][:8],
            "sample_desc": group["descs"][0] if group["descs"] else "",
            "board_hit_count": board_hits.get(group["name"], 0),
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["hot_total"],
            row["stock_count"],
            row["hot_max"],
            row["board_hit_count"],
            row["name"],
        ),
        reverse=True,
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def _build_kpl_theme_hits(items: list[dict[str, Any]]) -> dict[str, int]:
    hit_map: defaultdict[str, int] = defaultdict(int)
    for item in items or []:
        raw_text = str(item.get("theme") or "").strip()
        if not raw_text:
            continue
        for part in [segment.strip() for segment in raw_text.replace("|", "/").replace("；", "/").replace(";", "/").split("/") if segment.strip()]:
            hit_map[part] += 1
    return dict(hit_map)


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
