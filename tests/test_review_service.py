import unittest

from chanlun_app.review_service import ReviewService


class FakeReviewDataClient:
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
                {"name": "银行概念", "rank": 1, "pct_chg": 6.1, "limit_count": 6, "open_num": 1, "count": 18},
                {"name": "互联网金融", "rank": 2, "pct_chg": 4.9, "limit_count": 4, "open_num": 2, "count": 26},
            ],
        }

    def get_hot_money_list(self, name=None, force_refresh=False):
        return [
            {"name": "北京帮", "desc": "示例游资", "orgs": "中国中金财富证券有限公司北京宋庄路证券营业部"},
            {"name": "网红席位", "desc": "示例游资", "orgs": "国信证券股份有限公司浙江互联网分公司"},
        ]


class ReviewServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = ReviewService(data_client=FakeReviewDataClient())

    def test_overview_aggregates_focus_lists(self):
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
        self.assertEqual(result["focus_stocks"][0]["name"], "平安银行")
        self.assertIn("今天涨停", result["notes"]["summary"])


if __name__ == "__main__":
    unittest.main()
