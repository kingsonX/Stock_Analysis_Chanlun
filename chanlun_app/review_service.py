from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from .ai_profile import AIProviderError, ClaudeProfileExplainer
from .data_provider import DataProviderError, TushareClient, _is_tushare_rate_limit_error


class ReviewService:
    def __init__(self, data_client: TushareClient | None = None, ai_explainer: ClaudeProfileExplainer | None = None):
        self.data_client = data_client or TushareClient()
        self.ai_explainer = ai_explainer or ClaudeProfileExplainer()

    def overview(self, trade_date: str | None = None, include_ai: bool = False) -> dict[str, Any]:
        top_list = self.data_client.get_top_list(trade_date)
        market_indices = {"trade_date": trade_date or "", "items": []}
        try:
            market_indices = self.data_client.get_market_indices(trade_date)
        except DataProviderError:
            market_indices = {"trade_date": trade_date or "", "items": []}
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
        emotion_cycle = _build_emotion_cycle(
            limit_groups,
            limit_step.get("items", []),
            market_indices.get("items", []),
        )

        result = {
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
            "market_indices": market_indices,
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
            "emotion_cycle": emotion_cycle,
            "notes": _build_review_notes(limit_groups, focus_boards, focus_stocks),
        }

        if not include_ai:
            result["ai_review"] = {"status": "idle", "message": ""}
            return result

        return self.explain_overview(result)

    def explain_overview(self, review_payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(review_payload or {})
        try:
            ai_review = self.ai_explainer.explain_review(result)
            result["ai_review"] = ai_review
            result["focus_boards"] = _merge_ai_focus_boards(
                result.get("focus_boards", []),
                ai_review.get("analysis", {}).get("focus_boards"),
            )
            result["focus_stocks"] = _merge_ai_focus_stocks(
                result.get("focus_stocks", []),
                ai_review.get("analysis", {}).get("focus_stocks"),
            )
        except AIProviderError as exc:
            result["ai_review"] = {"status": "error", "message": exc.message}

        return result


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
    for rank, item in enumerate(sorted(items or [], key=lambda row: (_num(row, "rank"), -_board_limit_count(row), -_num(row, "pct_chg"))), start=1):
        boards.append(
            {
                "ts_code": str(item.get("ts_code", "") or "").strip(),
                "name": item.get("name", ""),
                "rank": int(_num(item, "rank")) or rank,
                "pct_chg": _num(item, "pct_chg"),
                "limit_count": _board_limit_count(item),
                "chain_count": _board_chain_count(item),
                "open_num": int(_num(item, "open_num")),
                "count": int(_num(item, "count")),
                "days": int(_num(item, "days")),
                "up_stat": str(item.get("up_stat", "") or "").strip(),
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


def _build_emotion_cycle(
    limit_groups: dict[str, list[dict[str, Any]]],
    ladder_items: list[dict[str, Any]],
    market_indices: list[dict[str, Any]],
) -> dict[str, Any]:
    up_count = len(limit_groups.get("up") or [])
    down_count = len(limit_groups.get("down") or [])
    burst_count = len(limit_groups.get("burst") or [])
    highest_board = _highest_board(ladder_items)
    positive_indices = sum(1 for item in market_indices[:3] if _num(item, "pct_chg") > 0)
    avg_index_chg = sum(_num(item, "pct_chg") for item in market_indices[:3]) / max(len(market_indices[:3]), 1)
    burst_ratio = burst_count / max(up_count + burst_count, 1)

    phase_key = "low_divergence"
    if up_count <= 20 and down_count >= 40:
        phase_key = "ice_point"
    elif down_count >= 35 and up_count < 55:
        phase_key = "down_acceleration"
    elif (burst_ratio >= 0.45 and down_count >= 15) or (down_count > up_count and up_count < 70):
        phase_key = "turn_weak"
    elif highest_board >= 5 and (burst_ratio >= 0.32 or down_count >= 12):
        phase_key = "high_divergence"
    elif up_count >= 120 and down_count <= 10 and highest_board >= 5 and burst_ratio <= 0.18:
        phase_key = "climax"
    elif up_count >= 90 and down_count <= 12 and positive_indices >= 2 and burst_ratio <= 0.30:
        phase_key = "acceleration"
    elif up_count >= 55 and down_count <= 22 and positive_indices >= 2:
        phase_key = "turn_strong"
    elif up_count >= 35 and down_count <= 35:
        phase_key = "low_divergence"

    phase_order = [
        "low_divergence",
        "turn_strong",
        "acceleration",
        "climax",
        "high_divergence",
        "turn_weak",
        "down_acceleration",
        "ice_point",
    ]
    phase_index = phase_order.index(phase_key)
    previous_phase_key = phase_order[phase_index - 1]
    next_phase_key = phase_order[(phase_index + 1) % len(phase_order)]
    phase = _emotion_phase_meta(phase_key)
    previous_phase = _emotion_phase_meta(previous_phase_key)
    next_phase = _emotion_phase_meta(next_phase_key)
    attack_score = max(
        0,
        min(
            100,
            round(
                up_count * 0.72
                + positive_indices * 9
                + min(highest_board, 8) * 4
                - down_count * 0.35
                - burst_ratio * 26
            ),
        ),
    )
    pressure_score = max(
        0,
        min(
            100,
            round(
                down_count * 1.35
                + burst_ratio * 55
                + max(highest_board - 4, 0) * 6
                + max(0, 40 - up_count) * 0.32
            ),
        ),
    )
    carry_score = max(
        0,
        min(
            100,
            round(
                highest_board * 10
                + up_count * 0.28
                - down_count * 0.5
                - burst_ratio * 42
            ),
        ),
    )
    bias_gap = attack_score - pressure_score
    if bias_gap >= 18:
        bias_label = "偏进攻"
    elif bias_gap <= -18:
        bias_label = "偏防守"
    else:
        bias_label = "均衡观察"
    confidence = max(42, min(95, 58 + round(abs(bias_gap) * 0.6) + (8 if phase_key in {"acceleration", "high_divergence", "turn_weak"} else 0)))
    basis = [
        f"涨停 {up_count} 家，跌停 {down_count} 家",
        f"炸板 {burst_count} 家，炸板率 {burst_ratio * 100:.0f}%",
        f"最高连板 {highest_board} 板",
        f"三大指数翻红 {positive_indices}/3，均涨幅 {avg_index_chg:.2f}%",
    ]
    return {
        "phase_key": phase_key,
        "phase": phase["phase"],
        "stage": phase["stage"],
        "direction": phase["direction"],
        "summary": phase["summary"],
        "action": phase["action"],
        "risk": phase["risk"],
        "focus": phase["focus"],
        "tone": phase["tone"],
        "bias_label": bias_label,
        "confidence": confidence,
        "previous_phase_key": previous_phase_key,
        "previous_phase": previous_phase["phase"],
        "next_phase_key": next_phase_key,
        "next_phase": next_phase["phase"],
        "basis": basis,
        "metrics": {
            "up_limit_count": up_count,
            "down_limit_count": down_count,
            "burst_count": burst_count,
            "burst_ratio": round(burst_ratio, 4),
            "highest_board": highest_board,
            "positive_indices": positive_indices,
            "avg_index_chg": round(avg_index_chg, 4),
            "attack_score": attack_score,
            "pressure_score": pressure_score,
            "carry_score": carry_score,
        },
    }


def _emotion_phase_meta(phase_key: str) -> dict[str, str]:
    phases = {
        "low_divergence": {
            "phase": "低位分歧",
            "stage": "弱势末期 / 试错前夜",
            "direction": "turning",
            "summary": "亏钱效应未完全退去，但分歧开始给新主线试错空间。",
            "action": "轻仓试错，只看最先主动的题材前排。",
            "risk": "若跌停和炸板继续扩散，低位分歧会重新滑向冰点。",
            "focus": "先盯最早回流的板块和前排首板，别急着满仓。",
            "tone": "turn",
        },
        "turn_strong": {
            "phase": "分歧转强（弱转强）",
            "stage": "修复确认",
            "direction": "rising",
            "summary": "涨停开始扩散、指数配合，赚钱效应从分歧里转强。",
            "action": "试错可提高到普通仓位，但仍只做主流前排。",
            "risk": "若前排隔日没有溢价，弱转强会变成假修复。",
            "focus": "看回封质量、次日溢价和板块是否同步放大。",
            "tone": "rise",
        },
        "acceleration": {
            "phase": "加速（大阳线）",
            "stage": "主流推进",
            "direction": "rising",
            "summary": "涨停扩散、跌停收敛，指数和题材共振，情绪处于加速段。",
            "action": "偏进攻，重点看主流核心和前排承接，不追后排。",
            "risk": "加速之后容易走向一致，次日重点看高位分歧是否放大。",
            "focus": "只做最强主流核心，不要把后排跟风当成强度延续。",
            "tone": "rise",
        },
        "climax": {
            "phase": "一致（高潮）",
            "stage": "高温一致",
            "direction": "rising",
            "summary": "赚钱效应高度一致，市场容易从主动进攻转为兑现博弈。",
            "action": "不再扩大追高，优先等分歧后的承接确认。",
            "risk": "高潮日次日若高标开盘缩量冲，容易出现强分歧。",
            "focus": "高潮看兑现，不看想象，重点盯高标缩量冲板后的承接。",
            "tone": "rise",
        },
        "high_divergence": {
            "phase": "高位分歧",
            "stage": "高位博弈",
            "direction": "falling",
            "summary": "高标和前排开始分歧，持筹者兑现意愿上升。",
            "action": "降仓看承接，只做确认后的核心回封。",
            "risk": "若炸板和跌停继续增加，会进入分歧转弱。",
            "focus": "核心看承接与回封，后排一旦掉队就不再硬接。",
            "tone": "fall",
        },
        "turn_weak": {
            "phase": "分歧转弱（强转弱）",
            "stage": "退潮确认",
            "direction": "falling",
            "summary": "亏钱效应开始压过赚钱效应，强势股补跌风险抬升。",
            "action": "防守优先，少做高位接力。",
            "risk": "若跌停扩散且指数不配合，退潮会加速。",
            "focus": "先保回撤，等亏钱效应释放完再找下一轮主动修复。",
            "tone": "fall",
        },
        "down_acceleration": {
            "phase": "分歧加速",
            "stage": "杀跌释放",
            "direction": "falling",
            "summary": "亏钱效应集中释放，市场进入加速出清。",
            "action": "控制回撤，只等恐慌充分后的新主线信号。",
            "risk": "不要把下跌中继当成冰点修复。",
            "focus": "先等恐慌宣泄充分，再找最先逆势走强的方向。",
            "tone": "fall",
        },
        "ice_point": {
            "phase": "冰点（一致）",
            "stage": "恐慌一致",
            "direction": "turning",
            "summary": "杀跌情绪接近一致，机会来自恐慌后的主动修复。",
            "action": "不急着抄底，先等最先走强的方向出现。",
            "risk": "冰点可以再冰点，必须等真实承接。",
            "focus": "等第一批主动转强的票和板块，不做情绪化抄底。",
            "tone": "turn",
        },
    }
    return phases.get(phase_key, phases["low_divergence"])


def _merge_ai_focus_boards(
    boards: list[dict[str, Any]],
    ai_items: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not ai_items:
        return boards
    board_map = {str(item.get("name", "")).strip(): dict(item) for item in boards}
    ordered: list[dict[str, Any]] = []
    for ai_item in ai_items:
        name = str(ai_item.get("name", "")).strip()
        if not name or name not in board_map:
            continue
        merged = dict(board_map[name])
        merged["ai_reason"] = str(ai_item.get("reason", "") or "").strip()
        merged["ai_action"] = str(ai_item.get("action", "") or "").strip()
        ordered.append(merged)
        board_map.pop(name, None)
    ordered.extend(board_map.values())
    return ordered[:10]


def _merge_ai_focus_stocks(
    stocks: list[dict[str, Any]],
    ai_items: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not ai_items:
        return stocks
    stock_map: dict[str, dict[str, Any]] = {}
    for item in stocks:
        key = str(item.get("ts_code", "")).strip() or str(item.get("name", "")).strip()
        if key:
            stock_map[key] = dict(item)

    ordered: list[dict[str, Any]] = []
    for ai_item in ai_items:
        key = str(ai_item.get("ts_code", "")).strip() or str(ai_item.get("name", "")).strip()
        if not key or key not in stock_map:
            continue
        merged = dict(stock_map[key])
        merged["ai_reason"] = str(ai_item.get("reason", "") or "").strip()
        merged["ai_action"] = str(ai_item.get("action", "") or "").strip()
        if str(ai_item.get("name", "")).strip():
            merged["name"] = str(ai_item.get("name", "")).strip()
        ordered.append(merged)
        stock_map.pop(key, None)
    ordered.extend(stock_map.values())
    return ordered[:12]


def _highest_board(items: list[dict[str, Any]]) -> int:
    return max((_ladder_count(item) for item in items or []), default=0)


def _board_watch_reason(item: dict[str, Any]) -> str:
    parts = [f"涨停家数 {_board_limit_count(item)}"]
    chain_count = _board_chain_count(item)
    if chain_count > 0:
        parts.append(f"连板家数 {chain_count}")
    sample_count = int(_num(item, "count"))
    if sample_count > 0:
        parts.append(f"板块样本 {sample_count}")
    up_stat = str(item.get("up_stat", "") or "").strip()
    if up_stat:
        parts.append(f"高标 {up_stat}")
    days = int(_num(item, "days"))
    if days > 0:
        parts.append(f"连续上榜 {days} 天")
    parts.append(f"涨幅 {(_num(item, 'pct_chg')):.2f}%")
    return "，".join(parts) + "。"


def _board_limit_count(item: dict[str, Any]) -> int:
    return int(_num(item, "up_nums")) or int(_num(item, "limit_count"))


def _board_chain_count(item: dict[str, Any]) -> int:
    return int(_num(item, "cons_nums")) or int(_num(item, "open_num"))


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
