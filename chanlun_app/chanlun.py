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


def analyze_klines(klines: list[dict[str, Any]], level: str = "daily") -> dict[str, Any]:
    raw_bars = _to_raw_bars(klines)
    if len(raw_bars) < 7:
        return {
            "meta": _meta(level, len(raw_bars), 0, note="K线数量不足，无法形成稳定缠论结构。"),
            "klines": [asdict(bar) for bar in raw_bars],
            "indicators": {
                "macd": _macd_indicator(raw_bars),
                "bbi": _bbi_indicator(raw_bars),
            },
            "merged_klines": [],
            "fractals": [],
            "strokes": [],
            "centers": [],
            "divergences": [],
            "signals": [],
        }

    merged = merge_inclusions(raw_bars)
    fractals = identify_fractals(merged)
    macd = _macd_indicator(raw_bars)
    hist = np.array([item["hist"] for item in macd], dtype=float)
    strokes = build_strokes(fractals, hist)
    centers = build_centers(strokes)
    divergences = detect_divergences(strokes, centers)
    signals = detect_signals(strokes, centers, divergences, level)

    return {
        "meta": _meta(
            level,
            len(raw_bars),
            len(merged),
            counts={
                "fractals": len(fractals),
                "strokes": len(strokes),
                "centers": len(centers),
                "divergences": len(divergences),
                "signals": len(signals),
            },
        ),
        "klines": [asdict(bar) for bar in raw_bars],
        "indicators": {
            "macd": macd,
            "bbi": _bbi_indicator(raw_bars),
        },
        "merged_klines": [asdict(bar) for bar in merged],
        "fractals": [asdict(item) for item in fractals],
        "strokes": [asdict(item) for item in strokes],
        "centers": [asdict(item) for item in centers],
        "divergences": [asdict(item) for item in divergences],
        "signals": [asdict(item) for item in signals],
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

        raw_span = abs(item.raw_index - last.raw_index) + 1
        if raw_span >= min_raw_bars:
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
        momentum_strength = float(np.sum(np.abs(macd_hist[lo : hi + 1]))) if len(macd_hist) else 0.0
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
                momentum_strength=momentum_strength,
            )
        )
    return strokes


def build_centers(strokes: list[Stroke]) -> list[Center]:
    centers: list[Center] = []
    for i in range(0, len(strokes) - 2):
        group = strokes[i : i + 3]
        overlap_low = max(stroke.low for stroke in group)
        overlap_high = min(stroke.high for stroke in group)
        if overlap_low <= overlap_high:
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

    def add_signal(signal_type: str, side: str, stroke_index: int, date: str, price: float, reason: str, confidence: str) -> None:
        key = (signal_type, side, stroke_index)
        if key in signal_keys:
            return
        signal_keys.add(key)
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
                )

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
        "rule_profile": "内置严谨口径：包含处理后识别顶底分型，成笔至少 5 根原始 K 线跨度。",
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
