import unittest

from chanlun_app.review_service import ReviewService, _build_emotion_cycle
from chanlun_app.ai_profile import ClaudeProfileExplainer


class FakeReviewDataClient:
    def get_market_indices(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {"ts_code": "000001.SH", "name": "上证综指", "close": 3200.0, "pct_chg": 0.85, "pb": 1.32},
                {"ts_code": "399001.SZ", "name": "深证成指", "close": 10350.0, "pct_chg": 1.42, "pb": 2.08},
                {"ts_code": "399006.SZ", "name": "创业板指", "close": 2100.0, "pct_chg": 2.18, "pb": 3.21},
            ],
        }

    def get_top_list(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {"ts_code": "000001.SZ", "name": "平安银行", "net_amount": 420000000.0, "pct_change": 9.2, "reason": "日涨幅偏离值达7%"},
                {"ts_code": "300059.SZ", "name": "东方财富", "net_amount": 210000000.0, "pct_change": 7.4, "reason": "日换手率达20%"},
            ],
        }

    def get_hot_money_detail(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {
                    "ts_code": "000001.SZ",
                    "ts_name": "平安银行",
                    "buy_amount": 260000000.0,
                    "sell_amount": 80000000.0,
                    "net_amount": 180000000.0,
                    "hm_name": "北京帮",
                    "hm_orgs": "中国中金财富证券有限公司北京宋庄路证券营业部",
                    "tag": "净买入",
                },
                {
                    "ts_code": "300059.SZ",
                    "ts_name": "东方财富",
                    "buy_amount": 150000000.0,
                    "sell_amount": 60000000.0,
                    "net_amount": 90000000.0,
                    "hm_name": "网红席位",
                    "hm_orgs": "国信证券股份有限公司浙江互联网分公司",
                    "tag": "净买入",
                },
            ],
        }

    def get_limit_list(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {"ts_code": "000001.SZ", "name": "平安银行", "limit": "U", "limit_times": 2, "strth": 98.0, "open_times": 0, "fd_amount": 0.0},
                {"ts_code": "300059.SZ", "name": "东方财富", "limit": "U", "limit_times": 1, "strth": 84.0, "open_times": 1, "fd_amount": 12000000.0},
                {"ts_code": "600000.SH", "name": "浦发银行", "limit": "Z", "open_times": 3, "fd_amount": 23000000.0},
                {"ts_code": "000002.SZ", "name": "万科A", "limit": "D", "pct_chg": -10.0},
            ],
        }

    def get_limit_step(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {"ts_code": "000001.SZ", "name": "平安银行", "nums": 3, "limit_times": 3, "pct_chg": 9.2, "concept": "银行概念,中字头"},
                {"ts_code": "300059.SZ", "name": "东方财富", "nums": 2, "limit_times": 2, "pct_chg": 7.4, "concept": "证券,互联网金融"},
            ],
        }

    def get_limit_concept_list(self, trade_date=None):
        return {
            "trade_date": trade_date or "20260515",
            "items": [
                {"ts_code": "885001.TI", "name": "银行概念", "rank": 1, "pct_chg": 6.1, "up_nums": 6, "cons_nums": 2, "up_stat": "3天2板", "days": 3, "count": 18},
                {"ts_code": "885002.TI", "name": "互联网金融", "rank": 2, "pct_chg": 4.9, "up_nums": 4, "cons_nums": 1, "up_stat": "2天2板", "days": 2, "count": 26},
            ],
        }

    def get_hot_money_list(self, name=None, force_refresh=False):
        return [
            {"name": "北京帮", "desc": "示例游资", "orgs": "中国中金财富证券有限公司北京宋庄路证券营业部"},
            {"name": "网红席位", "desc": "示例游资", "orgs": "国信证券股份有限公司浙江互联网分公司"},
        ]


class FakeReviewExplainer(ClaudeProfileExplainer):
    def __init__(self):
        super().__init__(api_key="test-key", base_url="https://ark.cn-beijing.volces.com/api/coding/v3", model="doubao-seed-2-0-lite")

    def explain_review(self, review_payload):
        self.last_payload = review_payload
        return {
            "status": "ok",
            "provider": "火山方舟",
            "model": "doubao-seed-2-0-lite",
            "facts": {"trade_date": review_payload.get("trade_date", "")},
            "analysis": {
                "summary": "指数偏强，情绪修复，主线往金融与互金集中。",
                "market_stage": "主流试错",
                "index_review": {"summary": "指数共振修复。", "signals": ["上证与创业板同步翻红"]},
                "emotion_cycle": {"phase": "分歧转强（弱转强）", "summary": "赚钱效应回暖。", "signals": ["涨停多于跌停"]},
                "tape_review": {"summary": "热点集中。", "hot_themes": ["银行概念前排集中"], "fund_flow": ["龙虎榜净买入偏金融"], "limit_watch": ["高标 3 板观察分歧"]},
                "news_review": {"summary": "催化围绕金融与政策。", "catalysts": ["金融链消息发酵"], "ladder_focus": ["三板高度仍可观察"]},
                "watch_points": ["先看银行概念能否继续扩散"],
                "risk_points": ["若炸板增加先切防守"],
                "focus_boards": [{"name": "银行概念", "reason": "主流承接最好", "action": "先看前排封板质量"}],
                "focus_stocks": [{"ts_code": "000001.SZ", "name": "平安银行", "reason": "板块辨识度高", "action": "观察是否继续获得资金共振"}],
            },
        }


class ReviewServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = ReviewService(data_client=FakeReviewDataClient(), ai_explainer=FakeReviewExplainer())

    def test_overview_aggregates_focus_lists_without_ai_blocking(self):
        result = self.service.overview("20260515")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["trade_date"], "20260515")
        self.assertEqual(result["summary"]["dragon_count"], 2)
        self.assertEqual(result["summary"]["hot_money_count"], 2)
        self.assertEqual(result["summary"]["up_limit_count"], 2)
        self.assertEqual(result["summary"]["highest_board"], 3)
        self.assertEqual(result["ladder"][0]["continue_num"], 3)
        self.assertEqual(result["hot_money_trades"][0]["hot_money_label"], "北京帮")
        self.assertEqual(result["hot_money_trades"][0]["record_count"], 1)
        self.assertEqual(result["hot_money_stats"]["merged_count"], 2)
        self.assertEqual(result["focus_boards"][0]["name"], "银行概念")
        self.assertEqual(result["focus_boards"][0]["limit_count"], 6)
        self.assertEqual(result["focus_boards"][0]["chain_count"], 2)
        self.assertIn("高标 3天2板", result["focus_boards"][0]["watch_reason"])
        self.assertEqual(result["focus_stocks"][0]["name"], "平安银行")
        self.assertEqual(result["ai_review"]["status"], "idle")
        self.assertIn("今天涨停", result["notes"]["summary"])
        self.assertIn("phase", result["emotion_cycle"])

    def test_explain_overview_merges_ai_focus_lists(self):
        base = self.service.overview("20260515")
        result = self.service.explain_overview(base)

        self.assertEqual(result["ai_review"]["analysis"]["market_stage"], "主流试错")
        self.assertEqual(result["focus_boards"][0]["ai_action"], "先看前排封板质量")
        self.assertEqual(result["focus_stocks"][0]["ai_action"], "观察是否继续获得资金共振")

    def test_emotion_cycle_marks_acceleration_when_limit_effect_expands(self):
        cycle = _build_emotion_cycle(
            {
                "up": [{} for _ in range(102)],
                "down": [{} for _ in range(8)],
                "burst": [{} for _ in range(21)],
            },
            [{"nums": 4}],
            [{"pct_chg": 0.12}, {"pct_chg": 0.8}, {"pct_chg": 1.96}],
        )

        self.assertEqual(cycle["phase_key"], "acceleration")
        self.assertEqual(cycle["phase"], "加速（大阳线）")
        self.assertEqual(cycle["previous_phase_key"], "turn_strong")
        self.assertEqual(cycle["next_phase_key"], "climax")
        self.assertGreater(cycle["metrics"]["attack_score"], cycle["metrics"]["pressure_score"])


if __name__ == "__main__":
    unittest.main()
