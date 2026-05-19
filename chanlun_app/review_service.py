from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from .data_provider import DataProviderError, TushareClient, _is_tushare_rate_limit_error


class ReviewService:
    def __init__(self, data_client: TushareClient | None = None):
        self.data_client = data_client or TushareClient()

    def overview(self, trade_date: str | None = None) -> dict[str, Any]:
        top_list = self.data_client.get_top_list(trade_date)
        hot_money_detail = {"trade_date": trade_date or "", "items": []}
        hot_money_state = {"status": "ok", "message": ""}
        try:
            hot_money_detail = self.data_client.get_hot_money_detail(trade_date)
        except DataProviderError as exc:
            hot_money_state = {
                "status": "rate_limited" if _is_tushare_rate_limit_error(exc.message) else "error",
                "message": exc.message,
            }
        limit_list = self.data_client.get_limit_list(trade_date)
        limit_step = self.data_client.get_limit_step(trade_date)
        limit_concepts = self.data_client.get_limit_concept_list(trade_date)
        hot_money = []
        try:
            hot_money = self.data_client.get_hot_money_list()
        except DataProviderError:
            hot_money = []

        actual_trade_date = (
            top_list.get("trade_date")
            or hot_money_detail.get("trade_date")
            or limit_list.get("trade_date")
            or limit_step.get("trade_date")
            or limit_concepts.get("trade_date")
            or (trade_date or "")
        )

        limit_groups = _group_limit_items(limit_list.get("items", []))
        focus_boards = _build_focus_boards(limit_concepts.get("items", []))
        raw_hot_money_trades = _build_hot_money_trades(hot_money_detail.get("items", []), hot_money)
        merged_hot_money_trades = _merge_hot_money_trades(raw_hot_money_trades)
        focus_stocks = _build_focus_stocks(
            top_list.get("items", []),
            merged_hot_money_trades,
            limit_groups,
            limit_step.get("items", []),
            focus_boards,
        )

        return {
            "status": "ok",
            "trade_date": actual_trade_date,
            "summary": {
                "dragon_count": len(top_list.get("items", [])),
                "hot_money_count": len(raw_hot_money_trades),
                "up_limit_count": len(limit_groups["up"]),
                "down_limit_count": len(limit_groups["down"]),
                "burst_count": len(limit_groups["burst"]),
                "highest_board": _highest_board(limit_step.get("items", [])),
                "focus_board_count": len(focus_boards),
                "focus_stock_count": len(focus_stocks),
            },
            "dragon_tiger": top_list.get("items", []),
            "hot_money_state": hot_money_state,
            "hot_money_trades": merged_hot_money_trades,
            "hot_money_records": raw_hot_money_trades,
            "hot_money_stats": {
                "record_count": len(raw_hot_money_trades),
                "merged_count": len(merged_hot_money_trades),
            },
            "limit_lists": limit_groups,
            "ladder": _build_ladder(limit_step.get("items", [])),
            "focus_boards": focus_boards,
            "focus_stocks": focus_stocks,
            "notes": _build_review_notes(limit_groups, focus_boards, focus_stocks),
        }


def _build_hot_money_trades(items: list[dict[str, Any]], hot_money_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = _build_hot_money_lookup(hot_money_items)
    enriched: list[dict[str, Any]] = []
    for item in items or []:
        orgs = str(item.get("hm_orgs", "") or "").strip()
        names = _resolve_hot_money_names(orgs, lookup)
        primary_name = str(item.get("hm_name", "") or "").strip()
        hot_money_names = [primary_name] if primary_name else names
        if primary_name and primary_name not in names:
            hot_money_names.extend(names)
        row = dict(item)
        row["name"] = str(item.get("ts_name", "") or item.get("name", "") or "").strip()
        row["ts_name"] = row["name"]
        row["exalter"] = orgs
        row["hot_money_names"] = hot_money_names
        row["hot_money_label"] = " / ".join(hot_money_names[:3]) if hot_money_names else "-"
        enriched.append(row)
    return enriched


def _merge_hot_money_trades(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for item in items or []:
        ts_code = str(item.get("ts_code", "") or "").strip()
        name = str(item.get("name", "") or item.get("ts_name", "") or "").strip()
        key = ts_code or name
        if not key:
            continue
        bucket = buckets.setdefault(
            key,
            {
                "ts_code": ts_code,
                "name": name,
                "buy_amount": 0.0,
                "sell_amount": 0.0,
                "net_amount": 0.0,
                "hot_money_names": [],
                "hot_money_orgs": [],
                "record_count": 0,
                "tags": [],
                "trade_date": item.get("trade_date", ""),
            },
        )
        bucket["buy_amount"] += _num(item, "buy_amount")
        bucket["sell_amount"] += _num(item, "sell_amount")
        bucket["net_amount"] += _num(item, "net_amount")
        bucket["record_count"] += 1
        for hot_name in item.get("hot_money_names", []) or []:
            hot_name = str(hot_name or "").strip()
            if hot_name and hot_name not in bucket["hot_money_names"]:
                bucket["hot_money_names"].append(hot_name)
        for org in _split_hot_money_orgs(item.get("exalter") or item.get("hm_orgs")):
            if org not in bucket["hot_money_orgs"]:
                bucket["hot_money_orgs"].append(org)
        tag = str(item.get("tag", "") or "").strip()
        if tag and tag not in bucket["tags"]:
            bucket["tags"].append(tag)

    merged: list[dict[str, Any]] = []
    for bucket in buckets.values():
        hot_names = bucket["hot_money_names"]
        orgs = bucket["hot_money_orgs"]
        merged.append(
            {
                "ts_code": bucket["ts_code"],
                "name": bucket["name"],
                "buy_amount": round(bucket["buy_amount"], 2),
                "sell_amount": round(bucket["sell_amount"], 2),
                "net_amount": round(bucket["net_amount"], 2),
                "hot_money_names": hot_names,
                "hot_money_label": _summarize_names(hot_names),
                "exalter": _summarize_orgs(orgs),
                "hm_orgs": "；".join(orgs),
                "org_count": len(orgs),
                "record_count": bucket["record_count"],
                "tag": _summarize_tags(bucket["tags"], bucket["net_amount"]),
                "trade_date": bucket["trade_date"],
            }
        )
    return sorted(
        merged,
        key=lambda row: (abs(_num(row, "net_amount")), _num(row, "buy_amount")),
        reverse=True,
    )


def _build_hot_money_lookup(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = defaultdict(list)
    for item in items or []:
        name = str(item.get("name", "") or "").strip()
        if not name:
            continue
        for org in _split_hot_money_orgs(item.get("orgs", "")):
            if name not in lookup[org]:
                lookup[org].append(name)
    return lookup


def _resolve_hot_money_names(exalter: str, lookup: dict[str, list[str]]) -> list[str]:
    if not exalter:
        return []
    if exalter in lookup:
        return lookup[exalter][:3]
    names: list[str] = []
    for org, aliases in lookup.items():
        if not org or len(org) < 6:
            continue
        if org in exalter or exalter in org:
            for alias in aliases:
                if alias not in names:
                    names.append(alias)
    return names[:3]


def _split_hot_money_orgs(raw: Any) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    parts = [segment.strip() for segment in re.split(r"[、,，;；\n]+", text) if segment.strip()]
    result: list[str] = []
    for part in parts:
        if part not in result:
            result.append(part)
    return result


def _group_limit_items(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"up": [], "down": [], "burst": [], "other": []}
    for item in items or []:
        limit_flag = str(item.get("limit", "")).upper()
        if limit_flag == "U":
            groups["up"].append(item)
        elif limit_flag == "D":
            groups["down"].append(item)
        elif limit_flag == "Z":
            groups["burst"].append(item)
        else:
            groups["other"].append(item)
    groups["up"] = sorted(groups["up"], key=lambda row: (_num(row, "limit_times"), _num(row, "pct_chg")), reverse=True)
    groups["down"] = sorted(groups["down"], key=lambda row: _num(row, "pct_chg"))
    groups["burst"] = sorted(groups["burst"], key=lambda row: (_num(row, "open_times"), -_num(row, "fd_amount")), reverse=False)
    return groups


def _build_ladder(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ladder = []
    for item in sorted(items or [], key=lambda row: (_ladder_count(row), _num(row, "pct_chg")), reverse=True):
        continue_num = _ladder_count(item)
        limit_times = int(_num(item, "limit_times")) or continue_num
        ladder.append(
            {
                "ts_code": item.get("ts_code", ""),
                "name": item.get("name", ""),
                "continue_num": continue_num,
                "limit_times": limit_times,
                "pct_chg": _num(item, "pct_chg"),
                "turnover_rate": _num(item, "turnover_rate"),
                "amount": _num(item, "amount"),
                "up_stat": item.get("up_stat", ""),
                "industry": item.get("industry", ""),
                "concept": item.get("concept", ""),
                "change_tag": item.get("change_tag", ""),
            }
        )
    return ladder[:16]


def _build_focus_boards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boards = []
    for rank, item in enumerate(sorted(items or [], key=lambda row: (_num(row, "rank"), -_num(row, "limit_count"), -_num(row, "pct_chg"))), start=1):
        boards.append(
            {
                "name": item.get("name", ""),
                "rank": int(_num(item, "rank")) or rank,
                "pct_chg": _num(item, "pct_chg"),
                "limit_count": int(_num(item, "limit_count")),
                "open_num": int(_num(item, "open_num")),
                "count": int(_num(item, "count")),
                "turnover_rate": _num(item, "turnover_rate"),
                "watch_reason": _board_watch_reason(item),
            }
        )
    return boards[:10]


def _build_focus_stocks(
    top_list: list[dict[str, Any]],
    hot_money_trades: list[dict[str, Any]],
    limit_groups: dict[str, list[dict[str, Any]]],
    ladder: list[dict[str, Any]],
    focus_boards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    board_names = {item["name"] for item in focus_boards[:5]}
    scores: dict[str, dict[str, Any]] = {}

    def touch(ts_code: str, name: str) -> dict[str, Any]:
        if ts_code not in scores:
            scores[ts_code] = {"ts_code": ts_code, "name": name, "score": 0.0, "tags": [], "reasons": []}
        return scores[ts_code]

    for item in top_list[:20]:
        ts_code = item.get("ts_code", "")
        bucket = touch(ts_code, item.get("name", ""))
        net_amount = _num(item, "net_amount")
        bucket["score"] += max(net_amount, 0) / 1e8 + 6
        bucket["tags"].append("龙虎榜")
        bucket["reasons"].append(f"龙虎榜净额 {net_amount / 1e8:.2f} 亿")
        bucket["pct_chg"] = _num(item, "pct_change")

    for item in hot_money_trades[:20]:
        ts_code = item.get("ts_code", "")
        bucket = touch(ts_code, item.get("name", "") or item.get("ts_name", ""))
        net_amount = _num(item, "net_amount")
        bucket["score"] += max(net_amount, 0) / 1e8 + 5
        bucket["tags"].append("游资席位")
        label = str(item.get("hot_money_label", "") or item.get("hm_name", "") or "").strip()
        if label and label != "-":
            bucket["reasons"].append(f"{label} 净买入 {net_amount / 1e8:.2f} 亿")
        else:
            bucket["reasons"].append(f"游资净买入 {net_amount / 1e8:.2f} 亿")

    for item in ladder[:20]:
        ts_code = item.get("ts_code", "")
        bucket = touch(ts_code, item.get("name", ""))
        boards = {name.strip() for name in str(item.get("concept", "")).split(",") if name.strip()}
        continue_num = _ladder_count(item)
        bucket["score"] += continue_num * 4 + max(_num(item, "pct_chg"), 0) / 2
        bucket["tags"].append("连板梯队")
        bucket["reasons"].append(f"{continue_num} 连板")
        if boards & board_names:
            bucket["score"] += 6
            bucket["tags"].append("主线板块")
            bucket["reasons"].append("命中当前最强板块")

    for item in limit_groups["up"][:30]:
        ts_code = item.get("ts_code", "")
        bucket = touch(ts_code, item.get("name", ""))
        limit_times = int(_num(item, "limit_times"))
        bucket["score"] += limit_times * 1.6 + max(_num(item, "strth"), 0) / 10
        bucket["tags"].append("涨停前排")
        bucket["reasons"].append(f"涨停强度 {int(_num(item, 'strth'))}")
        if int(_num(item, "open_times")) == 0:
            bucket["score"] += 3
            bucket["reasons"].append("封板质量较好")

    result = []
    for item in sorted(scores.values(), key=lambda row: row["score"], reverse=True)[:12]:
        result.append(
            {
                "ts_code": item["ts_code"],
                "name": item["name"],
                "score": round(item["score"], 1),
                "tags": list(dict.fromkeys(item["tags"]))[:4],
                "reason": "，".join(dict.fromkeys(item["reasons"]))[:120],
                "verdict": _stock_verdict(item["score"]),
            }
        )
    return result


def _build_review_notes(
    limit_groups: dict[str, list[dict[str, Any]]],
    focus_boards: list[dict[str, Any]],
    focus_stocks: list[dict[str, Any]],
) -> dict[str, Any]:
    highest_board = focus_boards[0]["name"] if focus_boards else "暂无主线"
    highest_stock = focus_stocks[0]["name"] if focus_stocks else "暂无焦点股"
    highest_ladder = max((_ladder_count(item) for item in focus_stocks if "连板梯队" in item.get("tags", [])), default=0)
    return {
        "summary": f"今天涨停 {len(limit_groups['up'])} 家、跌停 {len(limit_groups['down'])} 家，最强板块看 {highest_board}，最强辨识度股票先看 {highest_stock}。",
        "watch_points": [
            f"先观察 {highest_board} 是否还能维持前排封板质量。",
            f"重点盯 {highest_stock} 是否继续获得龙虎榜或游资席位共振。",
            f"当前最高连板参考 {highest_ladder} 板，留意高位分歧是否扩散。",
        ],
        "risk_points": [
            "若炸板家数明显抬升，优先降低对高位接力的预期。",
            "若龙虎榜净买入前排转弱而跌停增多，先把复盘结论切回防守。",
        ],
    }


def _highest_board(items: list[dict[str, Any]]) -> int:
    return max((_ladder_count(item) for item in items or []), default=0)


def _board_watch_reason(item: dict[str, Any]) -> str:
    return (
        f"涨停家数 {int(_num(item, 'limit_count'))}，板块内样本 {int(_num(item, 'count'))}，"
        f"涨幅 {(_num(item, 'pct_chg')):.2f}% 。"
    )


def _stock_verdict(score: float) -> str:
    if score >= 24:
        return "重点盯"
    if score >= 14:
        return "可跟踪"
    return "观察"


def _summarize_names(names: list[str]) -> str:
    cleaned = [str(name or "").strip() for name in names if str(name or "").strip()]
    if not cleaned:
        return "-"
    head = " / ".join(cleaned[:2])
    if len(cleaned) > 2:
        return f"{head} 等{len(cleaned)}路"
    return head


def _summarize_orgs(orgs: list[str]) -> str:
    cleaned = [str(org or "").strip() for org in orgs if str(org or "").strip()]
    if not cleaned:
        return "-"
    head = "；".join(cleaned[:2])
    if len(cleaned) > 2:
        return f"{head} 等{len(cleaned)}席位"
    return head


def _summarize_tags(tags: list[str], net_amount: float) -> str:
    cleaned = [str(tag or "").strip() for tag in tags if str(tag or "").strip()]
    if cleaned:
        unique = list(dict.fromkeys(cleaned))
        head = " / ".join(unique[:2])
        if len(unique) > 2:
            return f"{head} 等{len(unique)}类"
        return head
    if net_amount > 0:
        return "净买入"
    if net_amount < 0:
        return "净卖出"
    return "平衡"


def _num(item: dict[str, Any], key: str) -> float:
    value = item.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _ladder_count(item: dict[str, Any]) -> int:
    for key in ("continue_num", "nums", "limit_times"):
        value = int(_num(item, key))
        if value > 0:
            return value
    up_stat = str(item.get("up_stat", "") or "")
    if up_stat:
        head = up_stat.split("/", 1)[0].strip()
        if head.isdigit():
            return int(head)
    return 0
