import unittest

import numpy as np

from chanlun_app.chanlun import (
    Fractal,
    MergedBar,
    Stroke,
    analyze_klines,
    build_centers,
    build_segments,
    build_strokes,
    detect_divergences,
    detect_signals,
    identify_fractals,
    merge_inclusions,
)
from chanlun_app.chanlun import RawBar


def raw(index, high, low, open_=None, close=None):
    return RawBar(
        index=index,
        date=f"202401{index + 1:02d}",
        open=open_ if open_ is not None else low,
        high=high,
        low=low,
        close=close if close is not None else high,
    )


def merged(index, high, low):
    return MergedBar(
        index=index,
        start_index=index,
        end_index=index,
        start_date=f"202401{index + 1:02d}",
        end_date=f"202401{index + 1:02d}",
        open=low,
        high=high,
        low=low,
        close=high,
        direction="up",
        raw_count=1,
    )


def fractal(fractal_type, raw_index, price):
    return Fractal(
        id=f"f{raw_index}",
        type=fractal_type,
        merged_index=raw_index,
        raw_index=raw_index,
        date=f"202401{raw_index + 1:02d}",
        price=price,
        high=price,
        low=price,
        strength=1,
    )


def stroke(idx, direction, start_price, end_price, low, high, strength=0.1):
    return Stroke(
        id=f"b{idx + 1}",
        direction=direction,
        start_fractal_id=f"f{idx}",
        end_fractal_id=f"f{idx + 1}",
        start_index=idx * 5,
        end_index=idx * 5 + 4,
        start_merged_index=idx * 2,
        end_merged_index=idx * 2 + 1,
        start_date=f"202401{idx + 1:02d}",
        end_date=f"202401{idx + 2:02d}",
        start_price=start_price,
        end_price=end_price,
        high=high,
        low=low,
        raw_span=5,
        price_change=end_price - start_price,
        price_strength=strength,
        momentum_strength=0,
        macd_red_area=0,
        macd_green_area=0,
        macd_dif_end=0,
        macd_dea_end=0,
        macd_hist_end=0,
        macd_zero_position="crossing",
    )


class ChanlunEngineTest(unittest.TestCase):
    def test_merge_inclusions_respects_up_direction(self):
        bars = [
            raw(0, 10, 8, close=9),
            raw(1, 11, 9, close=10),
            raw(2, 10.5, 9.5, close=10.2),
        ]

        result = merge_inclusions(bars)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[-1].direction, "up")
        self.assertEqual(result[-1].high, 11)
        self.assertEqual(result[-1].low, 9.5)
        self.assertEqual(result[-1].raw_count, 2)

    def test_identify_fractals_alternates(self):
        bars = [
            merged(0, 10, 8),
            merged(1, 12, 10),
            merged(2, 11, 9),
            merged(3, 13, 11),
            merged(4, 8, 6),
            merged(5, 10, 8),
        ]

        result = identify_fractals(bars)

        self.assertEqual([item.type for item in result], ["top", "bottom", "top", "bottom"])
        self.assertEqual(result[0].price, 12)
        self.assertEqual(result[-1].price, 6)

    def test_build_strokes_requires_five_raw_bars(self):
        macd = np.zeros(20)

        too_short = build_strokes([fractal("bottom", 0, 5), fractal("top", 3, 8)], macd)
        enough = build_strokes([fractal("bottom", 0, 5), fractal("top", 4, 8)], macd)

        self.assertEqual(too_short, [])
        self.assertEqual(len(enough), 1)
        self.assertEqual(enough[0].direction, "up")

    def test_build_centers_from_three_overlapping_strokes(self):
        strokes = [
            stroke(0, "up", 8, 12, 8, 12),
            stroke(1, "down", 12, 9, 9, 12),
            stroke(2, "up", 9, 13, 9, 13),
        ]

        centers = build_centers(strokes)

        self.assertEqual(len(centers), 1)
        self.assertEqual(centers[0].low, 9)
        self.assertEqual(centers[0].high, 12)
        self.assertEqual(centers[0].status, "forming")

    def test_build_segments_groups_three_strokes(self):
        strokes = [
            stroke(0, "up", 8, 12, 8, 12),
            stroke(1, "down", 12, 9, 9, 12),
            stroke(2, "up", 9, 13, 9, 13),
            stroke(3, "down", 13, 10, 10, 13),
            stroke(4, "up", 10, 14, 10, 14),
        ]

        segments = build_segments(strokes)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].stroke_ids, ["b1", "b2", "b3"])
        self.assertEqual(segments[-1].status, "active")

    def test_detect_divergence_and_first_signal(self):
        strokes = [
            stroke(0, "up", 8, 10, 8, 10, strength=0.2),
            stroke(1, "down", 10, 8.5, 8.5, 10, strength=0.1),
            stroke(2, "up", 8.5, 12, 8.5, 12, strength=0.08),
        ]

        divergences = detect_divergences(strokes)
        signals = detect_signals(strokes, [], divergences, "daily")

        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].side, "sell")
        self.assertEqual(divergences[0].evidence["previous_stroke_id"], "b1")
        self.assertEqual(divergences[0].evidence["current_stroke_id"], "b3")
        self.assertIn("previous_macd_red_area", divergences[0].evidence)
        self.assertIn("current_macd_green_area", divergences[0].evidence)
        self.assertIn("previous_dif_end", divergences[0].evidence)
        self.assertIn("current_dea_end", divergences[0].evidence)
        self.assertIn("current_zero_position", divergences[0].evidence)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].type, "一类卖点")
        self.assertEqual(signals[0].status, "candidate")
        self.assertGreater(signals[0].invalidation_price, 0)

    def test_analyze_returns_trend_and_signal_state_fields(self):
        klines = [
            {"index": item.index, "date": item.date, "open": item.open, "high": item.high, "low": item.low, "close": item.close}
            for item in [
                raw(0, 10, 8, close=9),
                raw(1, 12, 10, close=11),
                raw(2, 9, 7, close=8),
                raw(3, 13, 11, close=12),
                raw(4, 8, 6, close=7),
                raw(5, 14, 12, close=13),
                raw(6, 7, 5, close=6),
                raw(7, 15, 13, close=14),
                raw(8, 8, 6, close=7),
                raw(9, 16, 14, close=15),
                raw(10, 9, 7, close=8),
                raw(11, 17, 15, close=16),
            ]
        ]

        result = analyze_klines(klines, "daily")

        self.assertIn("segments", result)
        self.assertIn("trend", result)
        self.assertIn("backtest", result)
        self.assertIn("risk_cards", result)
        self.assertIn("position_label", result["trend"])
        self.assertIn("summary", result["backtest"])


if __name__ == "__main__":
    unittest.main()
