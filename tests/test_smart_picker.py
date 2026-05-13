import unittest

import pandas as pd

from chanlun_app.smart_picker import SmartPickerService


def sample_klines():
    values = [
        (10, 8, 9),
        (12, 10, 11),
        (9, 7, 8),
        (13, 11, 12),
        (8, 6, 7),
        (14, 12, 13),
        (7, 5, 6),
        (15, 13, 14),
        (8, 6, 7),
        (16, 14, 15),
        (9, 7, 8),
        (17, 15, 16),
    ]
    rows = []
    for idx, (high, low, close) in enumerate(values):
        rows.append(
            {
                "index": idx,
                "date": f"202401{idx + 1:02d}",
                "open": low,
                "high": high,
                "low": low,
                "close": close,
                "vol": 1000 + idx,
                "amount": 10000 + idx,
            }
        )
    return rows


class FakeStock:
    def __init__(self, symbol="000001", name="平安银行", ts_code="000001.SZ", industry="银行"):
        self.symbol = symbol
        self.name = name
        self.ts_code = ts_code
        self.industry = industry

    def as_dict(self):
        return {
            "ts_code": self.ts_code,
            "symbol": self.symbol,
            "name": self.name,
            "industry": self.industry,
            "area": "深圳",
            "market": "主板",
            "exchange": "SZSE",
            "list_date": "19910403",
            "cnspell": "PAYH",
        }


class FakeDataClient:
    def __init__(self):
        self.records = {
            "000001": FakeStock(symbol="000001", name="平安银行", ts_code="000001.SZ", industry="银行"),
            "000001.SZ": FakeStock(symbol="000001", name="平安银行", ts_code="000001.SZ", industry="银行"),
            "平安银行": FakeStock(symbol="000001", name="平安银行", ts_code="000001.SZ", industry="银行"),
            "600000": FakeStock(symbol="600000", name="浦发银行", ts_code="600000.SH", industry="银行"),
            "600000.SH": FakeStock(symbol="600000", name="浦发银行", ts_code="600000.SH", industry="银行"),
            "浦发银行": FakeStock(symbol="600000", name="浦发银行", ts_code="600000.SH", industry="银行"),
            "300059": FakeStock(symbol="300059", name="东方财富", ts_code="300059.SZ", industry="证券"),
            "300059.SZ": FakeStock(symbol="300059", name="东方财富", ts_code="300059.SZ", industry="证券"),
            "东方财富": FakeStock(symbol="300059", name="东方财富", ts_code="300059.SZ", industry="证券"),
        }

    def resolve_stock(self, query):
        return self.records.get(query, self.records["000001"])

    def get_klines(self, ts_code, level, start_date, end_date):
        return sample_klines()

    def load_stocks(self, force_refresh=False):
        rows = [item.as_dict() for key, item in self.records.items() if "." in item.ts_code and key in {item.ts_code, item.name, item.symbol}]
        unique = {}
        for row in rows:
            unique[row["ts_code"]] = row
        return pd.DataFrame(list(unique.values()))


class FakeScreenProvider:
    def search(self, query):
        return {"query": query}

    def parse_response(self, result):
        query = result["query"]
        if "今日涨停" in query:
            return {
                "rows": [
                    {"股票代码": "000001", "股票简称": "平安银行", "涨跌幅": "10.0%", "成交额": "16.0亿", "换手率": "5.6%"},
                    {"股票代码": "300059", "股票简称": "东方财富", "涨跌幅": "9.9%", "成交额": "20.0亿", "换手率": "6.2%"},
                ],
                "total": 24,
                "description": "涨停强度",
                "parser_text": "",
            }
        if "涨幅大于5%" in query:
            return {
                "rows": [
                    {"股票代码": "000001", "股票简称": "平安银行", "涨跌幅": "10.0%", "成交额": "16.0亿", "换手率": "5.6%"},
                    {"股票代码": "600000", "股票简称": "浦发银行", "涨跌幅": "6.8%", "成交额": "11.0亿", "换手率": "4.3%"},
                    {"股票代码": "300059", "股票简称": "东方财富", "涨跌幅": "5.6%", "成交额": "20.0亿", "换手率": "6.2%"},
                ],
                "total": 88,
                "description": "高涨幅热度",
                "parser_text": "",
            }
        if "成交额大于10亿" in query:
            return {
                "rows": [
                    {"股票代码": "000001", "股票简称": "平安银行", "涨跌幅": "10.0%", "成交额": "16.0亿", "换手率": "5.6%"},
                    {"股票代码": "600000", "股票简称": "浦发银行", "涨跌幅": "6.8%", "成交额": "11.0亿", "换手率": "4.3%"},
                    {"股票代码": "300059", "股票简称": "东方财富", "涨跌幅": "5.6%", "成交额": "20.0亿", "换手率": "6.2%"},
                ],
                "total": 126,
                "description": "活跃成交",
                "parser_text": "",
            }
        if "今日跌停" in query:
            return {"rows": [{"股票代码": "000777", "股票简称": "中核科技", "涨跌幅": "-10.0%"}], "total": 3, "description": "跌停压力", "parser_text": ""}
        if "跌幅大于5%" in query:
            return {"rows": [{"股票代码": "000002", "股票简称": "万科A"}], "total": 12, "description": "下跌承压", "parser_text": ""}
        return {
            "rows": [
                {
                    "股票代码": "000001",
                    "股票简称": "平安银行",
                    "最新价": "10.22",
                    "涨跌幅": "10.0%",
                    "成交额": "16.0亿",
                    "换手率": "5.6%",
                },
                {
                    "股票代码": "600000",
                    "股票简称": "浦发银行",
                    "最新价": "9.88",
                    "涨跌幅": "6.8%",
                    "成交额": "11.0亿",
                    "换手率": "4.3%",
                },
                {
                    "股票代码": "300059",
                    "股票简称": "东方财富",
                    "最新价": "18.36",
                    "涨跌幅": "5.6%",
                    "成交额": "12.6亿",
                    "换手率": "6.2%",
                }
            ],
            "total": 3,
            "description": "测试选股条件",
            "parser_text": "银行股涨幅大于2%",
        }


class FakeNewsProvider:
    def search(self, query):
        return {"query": query}

    def parse_response(self, result):
        return {
            "items": [
                {
                    "title": "银行板块最新政策催化",
                    "date": "20260504",
                    "source": "测试源",
                    "type": "新闻",
                    "summary": "板块热度持续。",
                }
            ],
            "total": 1,
        }


class FakeWatchlistProvider:
    def __init__(self):
        self.last_manage = None

    def query(self):
        return {"status": "ok", "items": [{"code": "000001", "name": "平安银行"}], "total": 1}

    def manage(self, action="", target=""):
        self.last_manage = {"action": action, "target": target}
        return {"status": "ok", "action": action, "target": target, "message": "操作成功"}


class BrokenWatchlistProvider:
    def query(self):
        raise RuntimeError("watchlist boom")

    def manage(self, action="", target=""):
        return {"status": "ok", "action": action, "target": target, "message": "操作成功"}


class FakeProfileService:
    def build(self, stock, analysis):
        return {
            "profile": {
                "stance": "neutral",
                "stance_label": "候选观察",
                "headline": "结构可看，主流活跃，容量中等，风险可控。",
                "conclusion": "先观察。",
            },
            "mx_summary": {"status": "ok", "data": {"cards": []}},
            "news": {"status": "ok", "items": []},
            "market_scan": {"status": "ok", "cards": []},
        }


class SmartPickerServiceTest(unittest.TestCase):
    def setUp(self):
        self.watchlist = FakeWatchlistProvider()
        self.service = SmartPickerService(
            data_client=FakeDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )

    def test_overview_builds_market_stage(self):
        result = self.service.overview()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stage"]["label"], "主流活跃")
        self.assertEqual(result["stage"]["cycle"], "主升试错期")
        self.assertEqual(len(result["market_cards"]), 5)
        self.assertEqual(result["universe"]["label"], "全A股")
        self.assertTrue(result["theme_ladders"])
        self.assertTrue(result["leader_board"])

    def test_screen_builds_candidates(self):
        result = self.service.screen(query_text="银行股涨幅大于2%", level="daily", limit=4)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["candidates"][0]["stock"]["name"], "平安银行")
        self.assertTrue(result["candidates"][0]["overall"]["label"])
        self.assertTrue(result["candidates"][0]["structure"]["label"])
        self.assertEqual(result["candidates"][0]["quote"]["amount_value"], 1600000000.0)
        self.assertEqual(result["candidates"][0]["emotion"]["label"], "主流热点")
        self.assertEqual(result["candidates"][0]["leader"]["label"], "龙头候选")

    def test_candidate_detail_contains_profile_and_watchlist(self):
        result = self.service.candidate_detail(stock={"ts_code": "000001.SZ"}, level="weekly")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stock"]["name"], "平安银行")
        self.assertTrue(result["watchlist"]["in_watchlist"])
        self.assertEqual(result["profile"]["profile"]["stance_label"], "候选观察")
        self.assertIn("execution", result)
        self.assertEqual(result["execution"]["plan"]["title"], "交易计划")
        self.assertEqual(result["execution"]["discipline"]["title"], "纪律引擎")
        self.assertEqual(result["execution"]["review"]["title"], "复盘系统")

    def test_manage_watchlist_delegates_to_provider(self):
        result = self.service.manage_watchlist(action="add", target="平安银行")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(self.watchlist.last_manage["action"], "add")

    def test_candidate_detail_degrades_when_watchlist_fails(self):
        service = SmartPickerService(
            data_client=FakeDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=BrokenWatchlistProvider(),
            trading_profile=FakeProfileService(),
        )

        result = service.candidate_detail(stock={"ts_code": "000001.SZ"}, level="daily")

        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["watchlist"]["in_watchlist"])
        self.assertEqual(result["watchlist"]["status"], "error")


if __name__ == "__main__":
    unittest.main()
