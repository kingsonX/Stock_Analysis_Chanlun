from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import numpy as np


MIN_RAW_BARS_PER_STROKE = 5


@dataclass
class RawBar:
    index: int
    date: str
    open: float
    high: float
    low: float
    close: float
    vol: float = 0
    amount: float = 0


@dataclass
class MergedBar:
    index: int
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    open: float
    high: float
    low: float
    close: float
    direction: str
    raw_count: int


@dataclass
class Fractal:
    id: str
    type: str
    merged_index: int
    raw_index: int
    date: str
    price: float
    high: float
    low: float
    strength: float


@dataclass
class Stroke:
    id: str
    direction: str
    start_fractal_id: str
    end_fractal_id: str
    start_index: int
    end_index: int
    start_merged_index: int
    end_merged_index: int
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    high: float
    low: float
    raw_span: int
    price_change: float
    price_strength: float
    momentum_strength: float
    macd_red_area: float
    macd_green_area: float
    macd_dif_end: float
    macd_dea_end: float
    macd_hist_end: float
    macd_zero_position: str


@dataclass
class ActiveStroke:
    direction: str
    start_fractal_id: str
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    high: float
    low: float
    raw_span: int
    price_change: float
    price_strength: float
    status: str
    status_label: str


@dataclass
class Segment:
    id: str
    direction: str
    start_stroke_index: int
    end_stroke_index: int
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    high: float
    low: float
    stroke_ids: list[str]
    strength: float
    status: str
    status_label: str
    feature_sequence: list[dict[str, Any]]
    feature_gap: dict[str, Any]


@dataclass
class Center:
    id: str
    start_stroke_index: int
    end_stroke_index: int
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    low: float
    high: float
    direction: str
    stroke_ids: list[str]
    status: str
    status_label: str
    extension_count: int
    breakout_direction: str
    reason: str


@dataclass
class Divergence:
    id: str
    category: str
    label: str
    stroke_index: int
    compare_stroke_index: int
    direction: str
    side: str
    position: str
    date: str
    price: float
    previous_strength: float
    current_strength: float
    center_id: str
    reason: str
    evidence: dict[str, Any]


@dataclass
class Signal:
    id: str
    type: str
    side: str
    level: str
    date: str
    price: float
    stroke_index: int
    reason: str
    confidence: str
    status: str
    status_label: str
    invalidation_price: float
    confirmation: str
    observation: str


@dataclass
class MACenter:
    id: str
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    low: float
    high: float
    status: str
    status_label: str
    reason: str


@dataclass
class MASignal:
    id: str
    type: str
    side: str
    date: str
    index: int
    price: float
    status: str
    status_label: str
    reason: str


def analyze_klines(klines: list[dict[str, Any]], level: str = "daily") -> dict[str, Any]:
    raw_bars = _to_raw_bars(klines)
    macd = _macd_indicator(raw_bars)
    bbi = _bbi_indicator(raw_bars)
    ma5 = _ma_indicator(raw_bars, 5)
    ma10 = _ma_indicator(raw_bars, 10)
    ma20 = _ma_indicator(raw_bars, 20)
    ma_centers = build_ma_centers(raw_bars, ma5, ma10, ma20)
    ma_signals = build_ma_signals(raw_bars, ma5, ma10, ma20, ma_centers)
    if len(raw_bars) < 7:
        return {
            "meta": _meta(level, len(raw_bars), 0, note="K线数量不足，无法形成稳定缠论结构。"),
            "klines": [asdict(bar) for bar in raw_bars],
            "indicators": {
                "macd": macd,
                "bbi": bbi,
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
            },
            "merged_klines": [],
            "fractals": [],
            "strokes": [],
            "active_stroke": None,
            "segments": [],
            "centers": [],
            "divergences": [],
            "signals": [],
            "ma_centers": [asdict(item) for item in ma_centers],
            "ma_signals": [asdict(item) for item in ma_signals],
            "trend": _trend_profile(level, [], [], [], []),
            "backtest": _signal_backtest([], [], []),
            "risk_cards": _risk_cards([], _trend_profile(level, [], [], [], [])),
        }

    merged = merge_inclusions(raw_bars)
    fractals = identify_fractals(merged)
    hist = np.array([item["hist"] for item in macd], dtype=float)
    strokes = build_strokes(fractals, hist, macd)
    active_stroke = build_active_stroke(raw_bars, fractals)
    segments = build_segments(strokes)
    centers = build_centers(strokes)
    divergences = detect_divergences(strokes, centers)
    signals = detect_signals(strokes, centers, divergences, level)
    trend = _trend_profile(level, raw_bars, strokes, segments, centers)
    backtest = _signal_backtest(raw_bars, strokes, signals)
    risk_cards = _risk_cards(signals, trend)

    return {
        "meta": _meta(
            level,
            len(raw_bars),
            len(merged),
            counts={
                "fractals": len(fractals),
                "strokes": len(strokes),
                "active_stroke": 1 if active_stroke else 0,
                "segments": len(segments),
                "centers": len(centers),
                "divergences": len(divergences),
                "signals": len(signals),
                "ma_centers": len(ma_centers),
                "ma_signals": len(ma_signals),
            },
        ),
        "klines": [asdict(bar) for bar in raw_bars],
        "indicators": {
            "macd": macd,
            "bbi": bbi,
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
        },
        "merged_klines": [asdict(bar) for bar in merged],
        "fractals": [asdict(item) for item in fractals],
        "strokes": [asdict(item) for item in strokes],
        "active_stroke": asdict(active_stroke) if active_stroke else None,
        "segments": [asdict(item) for item in segments],
        "centers": [asdict(item) for item in centers],
        "divergences": [asdict(item) for item in divergences],
        "signals": [asdict(item) for item in signals],
        "ma_centers": [asdict(item) for item in ma_centers],
        "ma_signals": [asdict(item) for item in ma_signals],
        "trend": trend,
        "backtest": backtest,
        "risk_cards": risk_cards,
    }


def merge_inclusions(raw_bars: list[RawBar]) -> list[MergedBar]:
    merged: list[MergedBar] = []
    for raw in raw_bars:
        next_bar = MergedBar(
            index=len(merged),
            start_index=raw.index,
            end_index=raw.index,
            start_date=raw.date,
            end_date=raw.date,
            open=raw.open,
            high=raw.high,
            low=raw.low,
            close=raw.close,
            direction="flat",
            raw_count=1,
        )
        if not merged:
            merged.append(next_bar)
            continue

        current = merged[-1]
        if _contains(current, next_bar):
            direction = _current_direction(merged, next_bar)
            merged[-1] = _merge_two(current, next_bar, direction)
            continue

        next_bar.direction = _direction_between(current, next_bar)
        next_bar.index = len(merged)
        merged.append(next_bar)

    return merged


def identify_fractals(merged: list[MergedBar]) -> list[Fractal]:
    candidates: list[Fractal] = []
    for i in range(1, len(merged) - 1):
        left, mid, right = merged[i - 1], merged[i], merged[i + 1]
        if mid.high > left.high and mid.high > right.high and mid.low > left.low and mid.low > right.low:
            candidates.append(_fractal("top", mid, len(candidates)))
        elif mid.low < left.low and mid.low < right.low and mid.high < left.high and mid.high < right.high:
            candidates.append(_fractal("bottom", mid, len(candidates)))

    normalized: list[Fractal] = []
    for item in candidates:
        if not normalized:
            normalized.append(item)
            continue
        last = normalized[-1]
        if item.type == last.type:
            if _is_more_extreme(item, last):
                normalized[-1] = item
        else:
            normalized.append(item)

    for idx, item in enumerate(normalized):
        item.id = f"f{idx + 1}"
    return normalized


def build_strokes(
    fractals: list[Fractal],
    macd_hist: np.ndarray,
    macd_rows: list[dict[str, Any]] | None = None,
    min_raw_bars: int = MIN_RAW_BARS_PER_STROKE,
) -> list[Stroke]:
    pivots: list[Fractal] = []
    for item in fractals:
        if not pivots:
            pivots.append(item)
            continue

        last = pivots[-1]
        if item.type == last.type:
            if _is_more_extreme(item, last):
                pivots[-1] = item
            continue

        pivots.append(item)

    strokes: list[Stroke] = []
    for idx in range(1, len(pivots)):
        start, end = pivots[idx - 1], pivots[idx]
        direction = "up" if start.type == "bottom" and end.type == "top" else "down"
        high = max(start.price, end.price)
        low = min(start.price, end.price)
        price_change = end.price - start.price
        raw_span = abs(end.raw_index - start.raw_index) + 1
        price_strength = abs(price_change) / max(abs(start.price), 1.0)
        lo, hi = sorted((start.raw_index, end.raw_index))
        macd_evidence = _stroke_macd_evidence(macd_hist, macd_rows or [], lo, hi, end.raw_index)
        strokes.append(
            Stroke(
                id=f"b{idx}",
                direction=direction,
                start_fractal_id=start.id,
                end_fractal_id=end.id,
                start_index=start.raw_index,
                end_index=end.raw_index,
                start_merged_index=start.merged_index,
                end_merged_index=end.merged_index,
                start_date=start.date,
                end_date=end.date,
                start_price=start.price,
                end_price=end.price,
                high=high,
                low=low,
                raw_span=raw_span,
                price_change=price_change,
                price_strength=price_strength,
                momentum_strength=macd_evidence["hist_area"],
                macd_red_area=macd_evidence["red_area"],
                macd_green_area=macd_evidence["green_area"],
                macd_dif_end=macd_evidence["dif_end"],
                macd_dea_end=macd_evidence["dea_end"],
                macd_hist_end=macd_evidence["hist_end"],
                macd_zero_position=macd_evidence["zero_position"],
            )
        )
    return strokes


def build_active_stroke(raw_bars: list[RawBar], fractals: list[Fractal]) -> ActiveStroke | None:
    if not raw_bars or not fractals:
        return None

    last = fractals[-1]
    if last.raw_index >= raw_bars[-1].index:
        return None

    tail = raw_bars[last.raw_index + 1 :]
    if not tail:
        return None

    if last.type == "bottom":
        end_bar = max(tail, key=lambda item: item.high)
        direction = "up"
        end_price = end_bar.high
        high = end_price
        low = last.price
    else:
        end_bar = min(tail, key=lambda item: item.low)
        direction = "down"
        end_price = end_bar.low
        high = last.price
        low = end_price

    if end_bar.index <= last.raw_index:
        return None

    price_change = end_price - last.price
    return ActiveStroke(
        direction=direction,
        start_fractal_id=last.id,
        start_index=last.raw_index,
        end_index=end_bar.index,
        start_date=last.date,
        end_date=end_bar.date,
        start_price=last.price,
        end_price=end_price,
        high=high,
        low=low,
        raw_span=end_bar.index - last.raw_index + 1,
        price_change=price_change,
        price_strength=abs(price_change) / max(abs(last.price), 1.0),
        status="extending",
        status_label="延伸中",
    )


def build_segments(strokes: list[Stroke], min_strokes: int = 3) -> list[Segment]:
    segments: list[Segment] = []
    if len(strokes) < min_strokes:
        return segments

    start = 0
    while start + min_strokes - 1 < len(strokes):
        end = start + min_strokes - 1
        group = strokes[start : end + 1]
        first, last = group[0], group[-1]
        direction = "up" if last.end_price >= first.start_price else "down"
        high = max(stroke.high for stroke in group)
        low = min(stroke.low for stroke in group)
        strength = sum(_combined_strength(stroke) for stroke in group)
        is_active = end >= len(strokes) - 1
        feature_sequence = _segment_feature_sequence(group, direction, start)
        feature_gap = _segment_feature_gap(segments[-1] if segments else None, feature_sequence)
        segments.append(
            Segment(
                id=f"xd{len(segments) + 1}",
                direction=direction,
                start_stroke_index=start,
                end_stroke_index=end,
                start_index=first.start_index,
                end_index=last.end_index,
                start_date=first.start_date,
                end_date=last.end_date,
                start_price=first.start_price,
                end_price=last.end_price,
                high=high,
                low=low,
                stroke_ids=[stroke.id for stroke in group],
                strength=round(strength, 6),
                status="active" if is_active else "completed",
                status_label="当前线段" if is_active else "已完成",
                feature_sequence=feature_sequence,
                feature_gap=feature_gap,
            )
        )
        start += min_strokes - 1
    return segments


def _segment_feature_sequence(group: list[Stroke], segment_direction: str, start_stroke_index: int) -> list[dict[str, Any]]:
    feature_direction = "down" if segment_direction == "up" else "up"
    items: list[dict[str, Any]] = []
    for offset, stroke in enumerate(group):
        if stroke.direction != feature_direction:
            continue
        items.append(
            {
                "stroke_id": stroke.id,
                "stroke_index": start_stroke_index + offset,
                "direction": stroke.direction,
                "start_index": stroke.start_index,
                "end_index": stroke.end_index,
                "start_date": stroke.start_date,
                "end_date": stroke.end_date,
                "high": stroke.high,
                "low": stroke.low,
                "start_price": stroke.start_price,
                "end_price": stroke.end_price,
                "label": "特征序列",
            }
        )
    return items


def _segment_feature_gap(previous_segment: Segment | None, feature_sequence: list[dict[str, Any]]) -> dict[str, Any]:
    if previous_segment is None or not previous_segment.feature_sequence or not feature_sequence:
        return {}

    previous = previous_segment.feature_sequence[-1]
    current = feature_sequence[0]

    if current["low"] > previous["high"]:
        return {
            "label": "特征序列上缺口",
            "direction": "up",
            "start_index": previous["end_index"],
            "end_index": current["start_index"],
            "high": current["low"],
            "low": previous["high"],
        }
    if current["high"] < previous["low"]:
        return {
            "label": "特征序列下缺口",
            "direction": "down",
            "start_index": previous["end_index"],
            "end_index": current["start_index"],
            "high": previous["low"],
            "low": current["high"],
        }
    return {}


def build_centers(strokes: list[Stroke]) -> list[Center]:
    centers: list[Center] = []
    for i in range(0, len(strokes) - 2):
        group = strokes[i : i + 3]
        overlap_low = max(stroke.low for stroke in group)
        overlap_high = min(stroke.high for stroke in group)
        if overlap_low <= overlap_high:
            lifecycle = _center_lifecycle(i, i + 2, overlap_low, overlap_high, strokes)
            centers.append(
                Center(
                    id=f"zs{len(centers) + 1}",
                    start_stroke_index=i,
                    end_stroke_index=i + 2,
                    start_index=group[0].start_index,
                    end_index=group[-1].end_index,
                    start_date=group[0].start_date,
                    end_date=group[-1].end_date,
                    low=overlap_low,
                    high=overlap_high,
                    direction=group[-1].direction,
                    stroke_ids=[stroke.id for stroke in group],
                    status=lifecycle["status"],
                    status_label=lifecycle["status_label"],
                    extension_count=lifecycle["extension_count"],
                    breakout_direction=lifecycle["breakout_direction"],
                    reason=lifecycle["reason"],
                )
            )
    return centers


def detect_divergences(
    strokes: list[Stroke],
    centers: list[Center] | None = None,
    threshold: float = 0.88,
) -> list[Divergence]:
    divergences: list[Divergence] = []
    centers = centers or []

    for center in centers:
        entry_index = center.start_stroke_index - 1
        exit_index = center.end_stroke_index + 1
        if entry_index < 0 or exit_index >= len(strokes):
            continue

        entry_stroke = strokes[entry_index]
        exit_stroke = strokes[exit_index]
        if entry_stroke.direction != exit_stroke.direction:
            continue

        if exit_stroke.direction == "up":
            leaves_center = exit_stroke.end_price > center.high
            price_extended = exit_stroke.end_price > entry_stroke.end_price
        else:
            leaves_center = exit_stroke.end_price < center.low
            price_extended = exit_stroke.end_price < entry_stroke.end_price
        if not leaves_center or not price_extended:
            continue

        prior_same_direction_centers = _count_prior_center_exits(centers, strokes, center, exit_stroke.direction)
        category = "trend" if prior_same_direction_centers >= 2 else "consolidation"
        label = "趋势背驰" if category == "trend" else "盘整背驰"
        position = "趋势末端" if category == "trend" else "盘整中"
        divergence = _build_divergence(
            divergence_id=f"bc{len(divergences) + 1}",
            category=category,
            label=label,
            current=exit_stroke,
            previous=entry_stroke,
            current_index=exit_index,
            previous_index=entry_index,
            threshold=threshold,
            position=position,
            center_id=center.id,
            reason_prefix=f"{label}：中枢 {center.id} 的离开段 {exit_stroke.id} 与进入段 {entry_stroke.id} 同向比较",
        )
        if divergence is not None:
            divergences.append(divergence)

    for i in range(2, len(strokes)):
        current = strokes[i]
        previous = strokes[i - 2]
        if current.direction != previous.direction:
            continue

        divergence = _build_divergence(
            divergence_id=f"bc{len(divergences) + 1}",
            category="stroke_internal",
            label="线段内背驰",
            current=current,
            previous=previous,
            current_index=i,
            previous_index=i - 2,
            threshold=threshold,
            position="线段末端",
            center_id="",
            reason_prefix=f"线段内背驰：同方向笔 {current.id} 与 {previous.id} 比较",
        )
        if divergence is not None:
            divergences.append(divergence)
    return divergences


def detect_signals(
    strokes: list[Stroke],
    centers: list[Center],
    divergences: list[Divergence],
    level: str,
) -> list[Signal]:
    signals: list[Signal] = []
    signal_keys: set[tuple[str, str, int]] = set()
    divergences_by_stroke = {item.stroke_index: item for item in divergences}

    def add_signal(
        signal_type: str,
        side: str,
        stroke_index: int,
        date: str,
        price: float,
        reason: str,
        confidence: str,
        invalidation_price: float,
        confirmation: str,
        observation: str,
    ) -> None:
        key = (signal_type, side, stroke_index)
        if key in signal_keys:
            return
        signal_keys.add(key)
        status = _signal_state(strokes, side, stroke_index, invalidation_price)
        signals.append(
            Signal(
                id=f"s{len(signals) + 1}",
                type=signal_type,
                side=side,
                level=level,
                date=date,
                price=price,
                stroke_index=stroke_index,
                reason=reason,
                confidence=confidence,
                status=status["status"],
                status_label=status["status_label"],
                invalidation_price=round(float(invalidation_price), 6),
                confirmation=confirmation,
                observation=observation,
            )
        )

    for divergence in divergences:
        stroke = strokes[divergence.stroke_index]
        add_signal(
            "一类买点" if divergence.side == "buy" else "一类卖点",
            divergence.side,
            divergence.stroke_index,
            divergence.date,
            divergence.price,
            divergence.reason,
            "中",
            _signal_invalidation_price(divergence.side, stroke),
            "等待后续反向笔确认；若随后形成不创新低/不创新高的回试，可升级为二类买卖点。",
            f"证据绑定 {divergence.id}，比较 {divergence.evidence.get('previous_stroke_id')} 与 {divergence.evidence.get('current_stroke_id')}。",
        )

        second_index = divergence.stroke_index + 2
        if second_index < len(strokes):
            retest = strokes[second_index]
            if divergence.side == "buy" and retest.direction == "down" and retest.end_price > stroke.end_price:
                add_signal(
                    "二类买点",
                    "buy",
                    second_index,
                    retest.end_date,
                    retest.end_price,
                    "一类买点后的回调未跌破前低，形成二类买点候选。",
                    "中",
                    stroke.end_price,
                    "一类买点后的上攻成立，回调不破一买低点。",
                    "继续观察能否向上离开最近中枢；跌破一买低点则失效。",
                )
            elif divergence.side == "sell" and retest.direction == "up" and retest.end_price < stroke.end_price:
                add_signal(
                    "二类卖点",
                    "sell",
                    second_index,
                    retest.end_date,
                    retest.end_price,
                    "一类卖点后的反弹未突破前高，形成二类卖点候选。",
                    "中",
                    stroke.end_price,
                    "一类卖点后的下跌成立，反弹不破一卖高点。",
                    "继续观察能否向下离开最近中枢；突破一卖高点则失效。",
                )

    for center in centers:
        exit_index = center.end_stroke_index + 1
        retest_index = center.end_stroke_index + 2
        if retest_index >= len(strokes):
            continue
        exit_stroke = strokes[exit_index]
        retest = strokes[retest_index]
        if exit_stroke.direction == "up" and exit_stroke.end_price > center.high:
            if retest.direction == "down" and retest.end_price > center.high:
                add_signal(
                    "三类买点",
                    "buy",
                    retest_index,
                    retest.end_date,
                    retest.end_price,
                    "向上离开中枢后回调不回到中枢区间，形成三类买点候选。",
                    "中",
                    center.high,
                    "离开中枢后回调未回到中枢上沿。",
                    f"回到中枢上沿 {center.high:.4f} 下方则三买失效。",
                )
        elif exit_stroke.direction == "down" and exit_stroke.end_price < center.low:
            if retest.direction == "up" and retest.end_price < center.low:
                add_signal(
                    "三类卖点",
                    "sell",
                    retest_index,
                    retest.end_date,
                    retest.end_price,
                    "向下离开中枢后反抽不回到中枢区间，形成三类卖点候选。",
                    "中",
                    center.low,
                    "离开中枢后反抽未回到中枢下沿。",
                    f"回到中枢下沿 {center.low:.4f} 上方则三卖失效。",
                )

    for signal in signals:
        divergence = divergences_by_stroke.get(signal.stroke_index)
        if divergence and signal.id:
            signal.observation = f"{signal.observation} 背驰类型：{divergence.label}。"

    return sorted(signals, key=lambda item: (item.date, item.stroke_index))


def _build_divergence(
    divergence_id: str,
    category: str,
    label: str,
    current: Stroke,
    previous: Stroke,
    current_index: int,
    previous_index: int,
    threshold: float,
    position: str,
    center_id: str,
    reason_prefix: str,
) -> Divergence | None:
    previous_strength = _combined_strength(previous)
    current_strength = _combined_strength(current)
    strength_weaker = current_strength < previous_strength * threshold

    if current.direction == "up":
        price_extended = current.end_price > previous.end_price
        side = "sell"
        direction_text = "上涨"
        price_text = "创新高"
        price = current.end_price
    else:
        price_extended = current.end_price < previous.end_price
        side = "buy"
        direction_text = "下跌"
        price_text = "创新低"
        price = current.end_price

    if not price_extended or not strength_weaker:
        return None

    strength_ratio = current_strength / previous_strength if previous_strength else 0.0
    evidence = {
        "previous_stroke_id": previous.id,
        "current_stroke_id": current.id,
        "previous_direction": previous.direction,
        "current_direction": current.direction,
        "previous_price_strength": round(previous.price_strength, 6),
        "current_price_strength": round(current.price_strength, 6),
        "previous_macd_area": round(previous.momentum_strength, 6),
        "current_macd_area": round(current.momentum_strength, 6),
        "previous_macd_red_area": round(previous.macd_red_area, 6),
        "current_macd_red_area": round(current.macd_red_area, 6),
        "previous_macd_green_area": round(previous.macd_green_area, 6),
        "current_macd_green_area": round(current.macd_green_area, 6),
        "previous_dif_end": round(previous.macd_dif_end, 6),
        "current_dif_end": round(current.macd_dif_end, 6),
        "previous_dea_end": round(previous.macd_dea_end, 6),
        "current_dea_end": round(current.macd_dea_end, 6),
        "previous_hist_end": round(previous.macd_hist_end, 6),
        "current_hist_end": round(current.macd_hist_end, 6),
        "previous_zero_position": previous.macd_zero_position,
        "current_zero_position": current.macd_zero_position,
        "zero_position_changed": previous.macd_zero_position != current.macd_zero_position,
        "previous_strength": round(previous_strength, 6),
        "current_strength": round(current_strength, 6),
        "strength_ratio": round(strength_ratio, 6),
        "threshold": threshold,
        "price_extended": price_extended,
        "center_id": center_id,
        "position": position,
    }

    reason = (
        f"{reason_prefix}，{direction_text}价格{price_text}，但综合力度从 "
        f"{previous_strength:.4f} 降至 {current_strength:.4f}，低于前段的 {threshold:.0%}，"
        f"判定为{label}候选，位置：{position}。"
    )
    return Divergence(
        id=divergence_id,
        category=category,
        label=label,
        stroke_index=current_index,
        compare_stroke_index=previous_index,
        direction=current.direction,
        side=side,
        position=position,
        date=current.end_date,
        price=price,
        previous_strength=round(previous_strength, 6),
        current_strength=round(current_strength, 6),
        center_id=center_id,
        reason=reason,
        evidence=evidence,
    )


def _count_prior_center_exits(
    centers: list[Center],
    strokes: list[Stroke],
    current_center: Center,
    direction: str,
) -> int:
    count = 0
    for center in centers:
        if center.start_stroke_index > current_center.start_stroke_index:
            continue
        exit_index = center.end_stroke_index + 1
        if exit_index >= len(strokes):
            continue
        exit_stroke = strokes[exit_index]
        if exit_stroke.direction != direction:
            continue
        if direction == "up" and exit_stroke.end_price > center.high:
            count += 1
        elif direction == "down" and exit_stroke.end_price < center.low:
            count += 1
    return count


def _center_lifecycle(
    start_stroke_index: int,
    end_stroke_index: int,
    low: float,
    high: float,
    strokes: list[Stroke],
) -> dict[str, Any]:
    extension_count = 0
    breakout_direction = ""
    breakout_offset = -1
    subsequent = strokes[end_stroke_index + 1 :]

    for offset, stroke in enumerate(subsequent):
        if _ranges_overlap(stroke.low, stroke.high, low, high):
            extension_count += 1
        if stroke.end_price > high:
            breakout_direction = "up"
            breakout_offset = offset
            break
        if stroke.end_price < low:
            breakout_direction = "down"
            breakout_offset = offset
            break

    if not subsequent:
        return {
            "status": "forming",
            "status_label": "新生",
            "extension_count": 0,
            "breakout_direction": "",
            "reason": "三笔重叠刚形成，尚无离开段。",
        }

    if not breakout_direction:
        return {
            "status": "extending",
            "status_label": "延伸中",
            "extension_count": extension_count,
            "breakout_direction": "",
            "reason": f"后续 {extension_count} 笔仍与中枢区间重叠，暂按延伸处理中。",
        }

    retest = subsequent[breakout_offset + 1] if breakout_offset + 1 < len(subsequent) else None
    direction_label = "向上" if breakout_direction == "up" else "向下"
    if retest is None:
        return {
            "status": "leaving",
            "status_label": "离开中",
            "extension_count": extension_count,
            "breakout_direction": breakout_direction,
            "reason": f"已有{direction_label}离开段，尚未出现回抽/反抽确认。",
        }

    if _ranges_overlap(retest.low, retest.high, low, high):
        return {
            "status": "expanded",
            "status_label": "扩张/升级观察",
            "extension_count": extension_count + 1,
            "breakout_direction": breakout_direction,
            "reason": f"{direction_label}离开后回抽/反抽重新触及中枢，需观察是否扩张或升级。",
        }

    return {
        "status": "left_confirmed",
        "status_label": "离开确认",
        "extension_count": extension_count,
        "breakout_direction": breakout_direction,
        "reason": f"{direction_label}离开后回抽/反抽未回中枢，离开状态暂确认。",
    }


def _ranges_overlap(low_a: float, high_a: float, low_b: float, high_b: float) -> bool:
    return max(low_a, low_b) <= min(high_a, high_b)


def _signal_invalidation_price(side: str, stroke: Stroke) -> float:
    return stroke.low if side == "buy" else stroke.high


def _stroke_macd_evidence(
    macd_hist: np.ndarray,
    macd_rows: list[dict[str, Any]],
    start_index: int,
    end_index: int,
    pivot_index: int,
) -> dict[str, Any]:
    hist_slice = macd_hist[start_index : end_index + 1] if len(macd_hist) else np.array([])
    red_area = float(np.sum(hist_slice[hist_slice > 0])) if len(hist_slice) else 0.0
    green_area = float(np.sum(np.abs(hist_slice[hist_slice < 0]))) if len(hist_slice) else 0.0
    hist_area = red_area + green_area

    row = macd_rows[pivot_index] if 0 <= pivot_index < len(macd_rows) else {}
    dif = float(row.get("dif", 0) or 0)
    dea = float(row.get("dea", 0) or 0)
    hist = float(row.get("hist", 0) or 0)

    if dif > 0 and dea > 0:
        zero_position = "above"
    elif dif < 0 and dea < 0:
        zero_position = "below"
    else:
        zero_position = "crossing"

    return {
        "hist_area": hist_area,
        "red_area": red_area,
        "green_area": green_area,
        "dif_end": dif,
        "dea_end": dea,
        "hist_end": hist,
        "zero_position": zero_position,
    }


def _signal_state(strokes: list[Stroke], side: str, stroke_index: int, invalidation_price: float) -> dict[str, str]:
    later = strokes[stroke_index + 1 :]
    if side == "buy":
        invalid = any(stroke.end_price < invalidation_price or stroke.low < invalidation_price for stroke in later)
        confirmed = any(stroke.direction == "up" and stroke.end_price > strokes[stroke_index].end_price for stroke in later)
    else:
        invalid = any(stroke.end_price > invalidation_price or stroke.high > invalidation_price for stroke in later)
        confirmed = any(stroke.direction == "down" and stroke.end_price < strokes[stroke_index].end_price for stroke in later)

    if invalid:
        return {"status": "invalid", "status_label": "失效"}
    if confirmed:
        return {"status": "confirmed", "status_label": "确认"}
    return {"status": "candidate", "status_label": "候选"}


def _trend_profile(
    level: str,
    raw_bars: list[RawBar],
    strokes: list[Stroke],
    segments: list[Segment],
    centers: list[Center],
) -> dict[str, Any]:
    last_close = raw_bars[-1].close if raw_bars else None
    last_center = centers[-1] if centers else None
    last_segment = segments[-1] if segments else None
    last_stroke = strokes[-1] if strokes else None

    if len(centers) >= 2:
        previous, current = centers[-2], centers[-1]
        if current.low > previous.low and current.high > previous.high:
            trend_type = "趋势"
            direction = "up"
            label = "上涨趋势"
            reason = f"最近两个中枢重心上移：{previous.id} -> {current.id}。"
        elif current.low < previous.low and current.high < previous.high:
            trend_type = "趋势"
            direction = "down"
            label = "下跌趋势"
            reason = f"最近两个中枢重心下移：{previous.id} -> {current.id}。"
        else:
            trend_type = "盘整"
            direction = current.direction
            label = "中枢震荡"
            reason = f"最近两个中枢区间仍有重叠，按盘整观察。"
    elif last_center:
        trend_type = "盘整"
        direction = last_center.direction
        label = "单中枢盘整"
        reason = f"当前只有一个可识别中枢 {last_center.id}，趋势条件不足。"
    elif last_segment:
        trend_type = "未成中枢"
        direction = last_segment.direction
        label = "线段推进"
        reason = f"已有线段 {last_segment.id}，但尚未形成稳定中枢。"
    elif last_stroke:
        trend_type = "未成中枢"
        direction = last_stroke.direction
        label = "笔级推进"
        reason = f"已有笔 {last_stroke.id}，线段与中枢仍不足。"
    else:
        trend_type = "未成型"
        direction = ""
        label = "结构不足"
        reason = "K线数量或分型不足，无法定义走势类型。"

    position = _price_position(last_close, last_center) if last_close is not None else "unknown"
    return {
        "level": level,
        "type": trend_type,
        "direction": direction,
        "label": label,
        "reason": reason,
        "last_close": round(float(last_close), 6) if last_close is not None else None,
        "position": position,
        "position_label": _position_label(position),
        "last_center_id": last_center.id if last_center else "",
        "last_segment_id": last_segment.id if last_segment else "",
        "active_center_status": last_center.status_label if last_center else "无中枢",
    }


def _price_position(price: float, center: Center | None) -> str:
    if center is None:
        return "no_center"
    if price > center.high:
        return "above_center"
    if price < center.low:
        return "below_center"
    return "inside_center"


def _position_label(position: str) -> str:
    return {
        "above_center": "中枢上方",
        "below_center": "中枢下方",
        "inside_center": "中枢内部",
        "no_center": "无中枢",
    }.get(position, "未知")


def _signal_backtest(
    raw_bars: list[RawBar],
    strokes: list[Stroke],
    signals: list[Signal],
    horizon: int = 20,
) -> dict[str, Any]:
    trades: list[dict[str, Any]] = []
    for signal in signals:
        if signal.stroke_index < 0 or signal.stroke_index >= len(strokes):
            continue

        stroke = strokes[signal.stroke_index]
        signal_index = stroke.end_index
        future = [bar for bar in raw_bars if signal_index < bar.index <= signal_index + horizon]
        entry_price = max(float(signal.price), 0.000001)
        if not future:
            trades.append(
                {
                    "signal_id": signal.id,
                    "label": _signal_short_label(signal),
                    "side": signal.side,
                    "date": signal.date,
                    "entry_price": round(entry_price, 6),
                    "bars": 0,
                    "max_favorable_pct": 0,
                    "max_adverse_pct": 0,
                    "close_return_pct": 0,
                    "outcome": "待观察",
                }
            )
            continue

        if signal.side == "buy":
            favorable = max(bar.high for bar in future) - entry_price
            adverse = entry_price - min(bar.low for bar in future)
            close_return = future[-1].close - entry_price
        else:
            favorable = entry_price - min(bar.low for bar in future)
            adverse = max(bar.high for bar in future) - entry_price
            close_return = entry_price - future[-1].close

        favorable_pct = favorable / entry_price
        adverse_pct = max(adverse, 0) / entry_price
        close_return_pct = close_return / entry_price
        outcome = _backtest_outcome(signal, favorable_pct, adverse_pct)
        trades.append(
            {
                "signal_id": signal.id,
                "label": _signal_short_label(signal),
                "side": signal.side,
                "date": signal.date,
                "entry_price": round(entry_price, 6),
                "bars": len(future),
                "max_favorable_pct": round(favorable_pct, 6),
                "max_adverse_pct": round(adverse_pct, 6),
                "close_return_pct": round(close_return_pct, 6),
                "outcome": outcome,
            }
        )

    return {
        "horizon_bars": horizon,
        "summary": _backtest_summary(trades, signals),
        "trades": trades,
        "note": "复盘统计只按信号出现后的固定K线窗口观察顺向/逆向空间，不构成自动交易结论。",
    }


def _risk_cards(signals: list[Signal], trend: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for signal in signals[-8:]:
        entry = max(float(signal.price), 0.000001)
        invalidation = float(signal.invalidation_price or 0)
        risk_pct = abs(entry - invalidation) / entry if invalidation > 0 else 0
        risk_label = "风险偏宽" if risk_pct >= 0.08 else "正常" if risk_pct >= 0.03 else "窄止损"
        side_text = "买点" if signal.side == "buy" else "卖点"
        cards.append(
            {
                "signal_id": signal.id,
                "label": _signal_short_label(signal),
                "side": signal.side,
                "date": signal.date,
                "entry_price": round(entry, 6),
                "invalidation_price": round(invalidation, 6),
                "risk_pct": round(risk_pct, 6),
                "risk_label": risk_label,
                "status": signal.status,
                "status_label": signal.status_label,
                "trend_label": trend.get("label", ""),
                "position_label": trend.get("position_label", ""),
                "discipline": f"{side_text}先看失效价，未确认前按候选处理；跌破/突破失效价则退出该结构假设。",
                "trigger": signal.confirmation,
            }
        )
    return cards


def _backtest_summary(trades: list[dict[str, Any]], signals: list[Signal]) -> dict[str, Any]:
    observed = [item for item in trades if item["bars"] > 0]
    favorable_values = [item["max_favorable_pct"] for item in observed]
    adverse_values = [item["max_adverse_pct"] for item in observed]
    return {
        "signals": len(signals),
        "observed": len(observed),
        "confirmed": sum(1 for item in signals if item.status == "confirmed"),
        "invalid": sum(1 for item in signals if item.status == "invalid"),
        "buy": sum(1 for item in signals if item.side == "buy"),
        "sell": sum(1 for item in signals if item.side == "sell"),
        "avg_favorable_pct": round(float(np.mean(favorable_values)), 6) if favorable_values else 0,
        "avg_adverse_pct": round(float(np.mean(adverse_values)), 6) if adverse_values else 0,
    }


def _backtest_outcome(signal: Signal, favorable_pct: float, adverse_pct: float) -> str:
    if signal.status == "invalid":
        return "结构失效"
    if favorable_pct >= 0.03 and favorable_pct >= adverse_pct:
        return "顺向推进"
    if adverse_pct > favorable_pct:
        return "逆向压力"
    return "震荡观察"


def _signal_short_label(signal: Signal) -> str:
    side = "卖" if signal.side == "sell" else "买"
    if "三类" in signal.type:
        return f"{side}3"
    if "二类" in signal.type:
        return f"{side}2"
    if "一类" in signal.type:
        return f"{side}1"
    return side


def _to_raw_bars(klines: list[dict[str, Any]]) -> list[RawBar]:
    bars: list[RawBar] = []
    for idx, row in enumerate(klines):
        bars.append(
            RawBar(
                index=int(row.get("index", idx)),
                date=str(row["date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                vol=float(row.get("vol", 0)),
                amount=float(row.get("amount", 0)),
            )
        )
    return bars


def _meta(level: str, raw_count: int, merged_count: int, counts: dict[str, int] | None = None, note: str = "") -> dict[str, Any]:
    return {
        "level": level,
        "raw_count": raw_count,
        "merged_count": merged_count,
        "min_raw_bars_per_stroke": MIN_RAW_BARS_PER_STROKE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "counts": counts or {},
        "note": note,
        "rule_profile": "新笔口径：独立顶底分型直接成笔，同向更极端分型视为笔延伸，遇到反向独立分型判定前一笔结束。",
    }


def _contains(a: MergedBar, b: MergedBar) -> bool:
    return (a.high >= b.high and a.low <= b.low) or (b.high >= a.high and b.low <= a.low)


def _merge_two(a: MergedBar, b: MergedBar, direction: str) -> MergedBar:
    if direction == "down":
        high = min(a.high, b.high)
        low = min(a.low, b.low)
    else:
        high = max(a.high, b.high)
        low = max(a.low, b.low)

    return MergedBar(
        index=a.index,
        start_index=a.start_index,
        end_index=b.end_index,
        start_date=a.start_date,
        end_date=b.end_date,
        open=a.open,
        high=high,
        low=low,
        close=b.close,
        direction=direction,
        raw_count=a.raw_count + b.raw_count,
    )


def _current_direction(merged: list[MergedBar], incoming: MergedBar) -> str:
    if len(merged) >= 2:
        direction = _direction_between(merged[-2], merged[-1])
        if direction != "flat":
            return direction
    direction = _direction_between(merged[-1], incoming)
    if direction != "flat":
        return direction
    return merged[-1].direction if merged[-1].direction != "flat" else "up"


def _direction_between(a: MergedBar, b: MergedBar) -> str:
    if b.high > a.high and b.low > a.low:
        return "up"
    if b.high < a.high and b.low < a.low:
        return "down"
    if b.close > a.close:
        return "up"
    if b.close < a.close:
        return "down"
    return "flat"


def _fractal(fractal_type: str, bar: MergedBar, idx: int) -> Fractal:
    price = bar.high if fractal_type == "top" else bar.low
    neighbor_range = max(bar.high - bar.low, 0.000001)
    return Fractal(
        id=f"f{idx + 1}",
        type=fractal_type,
        merged_index=bar.index,
        raw_index=bar.end_index,
        date=bar.end_date,
        price=price,
        high=bar.high,
        low=bar.low,
        strength=round(neighbor_range, 6),
    )


def _is_more_extreme(candidate: Fractal, current: Fractal) -> bool:
    if candidate.type == "top":
        return candidate.price >= current.price
    return candidate.price <= current.price


def _macd_hist(closes: list[float]) -> np.ndarray:
    return _macd_arrays(closes)[2]


def _macd_indicator(raw_bars: list[RawBar]) -> list[dict[str, Any]]:
    dif, dea, hist = _macd_arrays([bar.close for bar in raw_bars])
    return [
        {
            "index": bar.index,
            "date": bar.date,
            "dif": round(float(dif[idx]), 6),
            "dea": round(float(dea[idx]), 6),
            "hist": round(float(hist[idx]), 6),
        }
        for idx, bar in enumerate(raw_bars)
    ]


def _bbi_indicator(raw_bars: list[RawBar]) -> list[dict[str, Any]]:
    closes = np.array([bar.close for bar in raw_bars], dtype=float)
    if len(closes) == 0:
        return []
    bbi = (_sma(closes, 3) + _sma(closes, 6) + _sma(closes, 12) + _sma(closes, 24)) / 4
    return [
        {
            "index": bar.index,
            "date": bar.date,
            "value": round(float(bbi[idx]), 6) if not np.isnan(bbi[idx]) else None,
        }
        for idx, bar in enumerate(raw_bars)
    ]


def _ma_indicator(raw_bars: list[RawBar], period: int) -> list[dict[str, Any]]:
    closes = np.array([bar.close for bar in raw_bars], dtype=float)
    if len(closes) == 0:
        return []
    values = _sma(closes, period)
    return [
        {
            "index": bar.index,
            "date": bar.date,
            "value": round(float(values[idx]), 6) if not np.isnan(values[idx]) else None,
        }
        for idx, bar in enumerate(raw_bars)
    ]


def build_ma_centers(
    raw_bars: list[RawBar],
    ma5_rows: list[dict[str, Any]],
    ma10_rows: list[dict[str, Any]],
    ma20_rows: list[dict[str, Any]],
) -> list[MACenter]:
    centers: list[MACenter] = []
    start = None
    center_high = float("-inf")
    center_low = float("inf")

    def flush(end_idx: int | None):
        nonlocal start, center_high, center_low
        if start is None or end_idx is None or end_idx - start + 1 < 3:
            start = None
            center_high = float("-inf")
            center_low = float("inf")
            return
        centers.append(
            MACenter(
                id=f"ma_zs{len(centers) + 1}",
                start_index=start,
                end_index=end_idx,
                start_date=raw_bars[start].date,
                end_date=raw_bars[end_idx].date,
                low=round(center_low, 6),
                high=round(center_high, 6),
                status="active" if end_idx >= raw_bars[-1].index else "completed",
                status_label="均线中枢观察" if end_idx >= raw_bars[-1].index else "均线中枢",
                reason="MA5/10/20 收敛缠绕，作为均线中枢观察区。",
            )
        )
        start = None
        center_high = float("-inf")
        center_low = float("inf")

    for idx, bar in enumerate(raw_bars):
        values = [ma5_rows[idx]["value"], ma10_rows[idx]["value"], ma20_rows[idx]["value"]]
        if any(value is None for value in values):
            flush(idx - 1)
            continue

        high = max(values)
        low = min(values)
        avg = sum(values) / 3
        tight = avg > 0 and (high - low) / avg <= 0.035
        if tight:
            if start is None:
                start = bar.index
            center_high = max(center_high, high)
            center_low = min(center_low, low)
        else:
            flush(idx - 1)
    flush(raw_bars[-1].index if raw_bars else None)
    return centers


def build_ma_signals(
    raw_bars: list[RawBar],
    ma5_rows: list[dict[str, Any]],
    ma10_rows: list[dict[str, Any]],
    ma20_rows: list[dict[str, Any]],
    centers: list[MACenter],
) -> list[MASignal]:
    signals: list[MASignal] = []
    last_buy1_index = -1
    last_sell1_index = -1
    last_buy2_index = -1
    last_sell2_index = -1
    last_buy3_center_id = ""
    last_sell3_center_id = ""

    def push(signal_type: str, side: str, bar: RawBar, price: float, reason: str):
        signals.append(
            MASignal(
                id=f"ma_s{len(signals) + 1}",
                type=signal_type,
                side=side,
                date=bar.date,
                index=bar.index,
                price=round(price, 6),
                status="candidate",
                status_label="均线辅助",
                reason=reason,
            )
        )

    for idx in range(1, len(raw_bars)):
        current = raw_bars[idx]
        previous = raw_bars[idx - 1]
        current_values = [ma5_rows[idx]["value"], ma10_rows[idx]["value"], ma20_rows[idx]["value"]]
        previous_values = [ma5_rows[idx - 1]["value"], ma10_rows[idx - 1]["value"], ma20_rows[idx - 1]["value"]]
        if any(value is None for value in current_values + previous_values):
            continue

        ma5, ma10, ma20 = current_values
        prev5, prev10, prev20 = previous_values
        bullish = ma5 >= ma10 >= ma20
        bearish = ma5 <= ma10 <= ma20
        golden_cross = prev5 <= prev10 and ma5 > ma10 and current.close >= ma5
        dead_cross = prev5 >= prev10 and ma5 < ma10 and current.close <= ma5

        if golden_cross:
            push("均线一类买点", "buy", current, current.low, "MA5 上穿 MA10，价格重新站回短均线。")
            last_buy1_index = current.index
        elif dead_cross:
            push("均线一类卖点", "sell", current, current.high, "MA5 下穿 MA10，价格跌回短均线下。")
            last_sell1_index = current.index

        if bullish and last_buy1_index >= 0 and current.index > last_buy1_index and last_buy2_index < last_buy1_index:
            if current.low <= ma10 * 1.01 and current.close >= ma10 and current.low >= ma20 * 0.99:
                push("均线二类买点", "buy", current, current.low, "多头均线下的第一次回踩 MA10/MA20。")
                last_buy2_index = current.index

        if bearish and last_sell1_index >= 0 and current.index > last_sell1_index and last_sell2_index < last_sell1_index:
            if current.high >= ma10 * 0.99 and current.close <= ma10 and current.high <= ma20 * 1.01:
                push("均线二类卖点", "sell", current, current.high, "空头均线下的第一次反抽 MA10/MA20。")
                last_sell2_index = current.index

        emitted_buy3 = False
        emitted_sell3 = False
        for center in centers:
            if current.index <= center.end_index:
                continue
            if bullish and not emitted_buy3 and previous.close <= center.high < current.close and last_buy3_center_id != center.id:
                push("均线三类买点", "buy", current, current.close, "价格向上离开均线中枢，且均线保持多头顺序。")
                last_buy3_center_id = center.id
                emitted_buy3 = True
            if bearish and not emitted_sell3 and previous.close >= center.low > current.close and last_sell3_center_id != center.id:
                push("均线三类卖点", "sell", current, current.close, "价格向下离开均线中枢，且均线保持空头顺序。")
                last_sell3_center_id = center.id
                emitted_sell3 = True

    return signals


def _sma(values: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(values), np.nan, dtype=float)
    for idx in range(period - 1, len(values)):
        result[idx] = float(np.mean(values[idx - period + 1 : idx + 1]))
    return result


def _macd_arrays(closes: list[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not closes:
        empty = np.array([])
        return empty, empty, empty
    values = np.array(closes, dtype=float)
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    dif = ema12 - ema26
    dea = _ema(dif, 9)
    hist = (dif - dea) * 2
    return dif, dea, hist


def _ema(values: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    result = np.zeros_like(values, dtype=float)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
    return result


def _combined_strength(stroke: Stroke) -> float:
    return stroke.price_strength + stroke.momentum_strength * 0.01
