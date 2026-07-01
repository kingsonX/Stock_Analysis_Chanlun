from __future__ import annotations

from typing import Any

from .data_provider import DataProviderError, TushareClient


class ThemeBoardService:
    def __init__(self, data_client: TushareClient | None = None):
        self.data_client = data_client or TushareClient()

    def overview(self, trade_date: str | None = None) -> dict[str, Any]:
        kpl_list_payload = self.data_client.get_kpl_list(trade_date=trade_date)
        kpl_list_items = kpl_list_payload.get("items", [])
        concept_items: list[dict[str, Any]] = []
        try:
            concept_items = self.data_client.get_kpl_concept_cons(
                trade_date=kpl_list_payload.get("trade_date") or trade_date
            ).get("items", [])
        except DataProviderError:
            concept_items = []

        items = _build_theme_rankings(kpl_list_items, concept_items)
        unique_stocks = {
            str(item.get("ts_code") or "").strip().upper()
            for item in kpl_list_items
            if str(item.get("ts_code") or "").strip()
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
            "trade_date": kpl_list_payload.get("trade_date") or trade_date or "",
            "summary": summary,
            "items": items,
        }

    def detail(self, trade_date: str | None = None, ts_code: str = "", name: str = "") -> dict[str, Any]:
        clean_ts_code = str(ts_code or "").strip().upper()
        clean_name = str(name or "").strip()
        if clean_ts_code or clean_name:
            try:
                payload = self.data_client.get_kpl_concept_cons(trade_date=trade_date, ts_code=clean_ts_code or None)
                items = payload.get("items", [])
                if clean_name:
                    items = [item for item in items if str(item.get("name") or "").strip() == clean_name]
                if clean_ts_code:
                    items = [item for item in items if str(item.get("ts_code") or "").strip().upper() == clean_ts_code]
                grouped = _build_concept_theme_rankings(items)
                if grouped:
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
                                "source": "kpl_concept_cons",
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
            except DataProviderError:
                pass

        fallback_payload = self.data_client.get_kpl_list(trade_date=trade_date)
        fallback_trade_date = str(fallback_payload.get("trade_date") or trade_date or "").strip()
        fallback_items = _build_theme_members_from_kpl_list(
            fallback_payload.get("items", []),
            theme_name=clean_name,
            theme_ts_code=clean_ts_code,
            trade_date=fallback_trade_date,
        )
        if not fallback_items:
            raise DataProviderError("没有获取到该题材的股票明细，请检查交易日期或题材名称。", 404)

        theme_name = clean_name or str(fallback_items[0].get("theme_name") or "").strip()
        hot_total = sum(_to_int(item.get("hot_num")) for item in fallback_items)
        return {
            "status": "ok",
            "trade_date": fallback_trade_date,
            "theme": {
                "ts_code": clean_ts_code,
                "name": theme_name,
                "stock_count": len(fallback_items),
                "hot_total": hot_total,
                "hot_avg": round(hot_total / len(fallback_items), 2) if fallback_items else 0,
                "top_stock": {
                    "name": fallback_items[0].get("name", ""),
                    "ts_code": fallback_items[0].get("ts_code", ""),
                    "hot_num": fallback_items[0].get("hot_num", 0),
                },
                "sample_desc": fallback_items[0].get("desc", ""),
                "source": "kpl_list",
            },
            "items": fallback_items,
        }


def _build_theme_rankings(kpl_list_items: list[dict[str, Any]], concept_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concept_rows = _build_concept_theme_rankings(concept_items)
    concept_by_name = {
        str(row.get("name") or "").strip(): row
        for row in concept_rows
        if str(row.get("name") or "").strip()
    }
    grouped: dict[str, dict[str, Any]] = {}
    for item in kpl_list_items or []:
        stock_code = str(item.get("ts_code") or "").strip().upper()
        stock_name = str(item.get("name") or "").strip()
        trade_date = str(item.get("trade_date") or "").strip()
        amount = _to_float(item.get("amount"))
        pct_chg = _to_float(item.get("pct_chg"))
        turnover_rate = _to_float(item.get("turnover_rate"))
        tag = str(item.get("tag") or "").strip()
        status = str(item.get("status") or "").strip()
        desc = str(item.get("lu_desc") or "").strip()
        for theme_name in _split_theme_names(item.get("theme")):
            group = grouped.setdefault(
                theme_name,
                {
                    "name": theme_name,
                    "trade_date": trade_date,
                    "stock_codes": set(),
                    "leaders": [],
                    "stock_names": [],
                    "descs": [],
                    "amount_total": 0.0,
                    "pct_total": 0.0,
                    "turnover_total": 0.0,
                },
            )
            if stock_code and stock_code not in group["stock_codes"]:
                group["stock_codes"].add(stock_code)
                group["stock_names"].append(stock_name or stock_code)
                group["amount_total"] += amount
                group["pct_total"] += pct_chg
                group["turnover_total"] += turnover_rate
                group["leaders"].append(
                    {
                        "name": stock_name,
                        "ts_code": stock_code,
                        "hot_num": int(round(amount / 10000.0)),
                        "amount": amount,
                        "pct_chg": pct_chg,
                        "tag": tag,
                        "status": status,
                    }
                )
            if desc and desc not in group["descs"]:
                group["descs"].append(desc)

    rows: list[dict[str, Any]] = []
    for theme_name, group in grouped.items():
        stock_count = len(group["stock_codes"])
        leaders = sorted(group["leaders"], key=lambda row: (row["amount"], row["pct_chg"], row["name"]), reverse=True)
        concept_row = concept_by_name.get(theme_name, {})
        proxy_hot_total = int(round(group["amount_total"] / 10000.0))
        hot_total = int(concept_row.get("hot_total", 0) or proxy_hot_total)
        row = {
            "ts_code": concept_row.get("ts_code", ""),
            "name": theme_name,
            "trade_date": group["trade_date"],
            "stock_count": stock_count,
            "hot_total": hot_total,
            "hot_avg": concept_row.get("hot_avg") or (round(hot_total / stock_count, 2) if stock_count else 0),
            "hot_max": concept_row.get("hot_max") or (leaders[0]["hot_num"] if leaders else 0),
            "top_stock": concept_row.get("top_stock") or (leaders[0] if leaders else {}),
            "stock_names": group["stock_names"][:8],
            "sample_desc": concept_row.get("sample_desc") or (group["descs"][0] if group["descs"] else ""),
            "board_hit_count": stock_count,
            "metric_source": "kpl_concept_cons" if concept_row else "kpl_list",
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["hot_total"],
            row["stock_count"],
            row["hot_max"],
            row["name"],
        ),
        reverse=True,
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def _build_concept_theme_rankings(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items or []:
        theme_code = str(item.get("ts_code") or "").strip().upper()
        theme_name = str(item.get("name") or "").strip()
        if not theme_name and not theme_code:
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
        rows.append(
            {
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
            }
        )
    return rows


def _build_theme_members_from_kpl_list(
    items: list[dict[str, Any]],
    theme_name: str,
    theme_ts_code: str,
    trade_date: str,
) -> list[dict[str, Any]]:
    clean_theme_name = str(theme_name or "").strip()
    members: list[dict[str, Any]] = []
    if not clean_theme_name:
        return members
    for item in items or []:
        themes = _split_theme_names(item.get("theme"))
        if clean_theme_name not in themes:
            continue
        amount = _to_float(item.get("amount"))
        pct_chg = _to_float(item.get("pct_chg"))
        turnover_rate = _to_float(item.get("turnover_rate"))
        tag = str(item.get("tag") or "").strip()
        status = str(item.get("status") or "").strip()
        desc = str(item.get("lu_desc") or "").strip()
        members.append(
            {
                "ts_code": str(item.get("ts_code") or "").strip().upper(),
                "name": str(item.get("name") or "").strip(),
                "theme_ts_code": theme_ts_code,
                "theme_name": clean_theme_name,
                "trade_date": str(item.get("trade_date") or trade_date or "").strip(),
                "hot_num": int(round(amount / 10000.0)),
                "desc": desc or f"{clean_theme_name} · {tag or '榜单'} {status}".strip(),
                "pct_chg": pct_chg,
                "amount": amount,
                "turnover_rate": turnover_rate,
                "tag": tag,
                "status": status,
                "source": "kpl_list",
            }
        )
    members.sort(key=lambda row: (row["hot_num"], row["pct_chg"], row["name"]), reverse=True)
    return members


def _split_theme_names(raw_value: Any) -> list[str]:
    text = str(raw_value or "").strip()
    if not text:
        return []
    normalized = text
    for token in ("、", "，", ",", "|", "/", "；", ";"):
        normalized = normalized.replace(token, "/")
    parts = [segment.strip() for segment in normalized.split("/") if segment.strip()]
    return parts


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
