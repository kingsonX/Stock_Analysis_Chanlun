import unittest
from importlib.util import find_spec

from chanlun_app.data_provider import DataProviderError, StockRecord
from chanlun_app.mx_provider import MXDataProvider

if find_spec("flask") is None:
    create_app = None
else:
    from chanlun_app import create_app


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


class FakeClient:
    def __init__(self):
        self.calls = []

    def search_stocks(self, query, limit=20):
        if query in {"平安", "000001", "平安银行"}:
            return [
                {
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "name": "平安银行",
                    "area": "深圳",
                    "industry": "银行",
                    "market": "主板",
                    "exchange": "SZSE",
                    "list_date": "19910403",
                    "cnspell": "PAYH",
                }
            ]
        return []

    def resolve_stock(self, value):
        matches = self.search_stocks(value)
        if not matches:
            raise DataProviderError("未找到股票", 404)
        return StockRecord(**matches[0])

    def get_klines(self, ts_code, level, start_date, end_date):
        self.last_call = {
            "ts_code": ts_code,
            "level": level,
            "start_date": start_date,
            "end_date": end_date,
        }
        self.calls.append(self.last_call)
        return sample_klines()


class FakeMxClient:
    def __init__(self):
        self.last_call = None

    def summary(self, ts_code="", name=""):
        self.last_call = {"ts_code": ts_code, "name": name}
        return {
            "stock": {"ts_code": ts_code, "name": name},
            "source": "mx-data",
            "cards": [
                {
                    "key": "quote",
                    "label": "行情",
                    "status": "ok",
                    "columns": ["date", "最新价"],
                    "rows": [{"date": "最新", "最新价": "10.00"}],
                }
            ],
        }


class FakeProfileClient:
    def __init__(self):
        self.last_call = None

    def build(self, stock, analysis):
        self.last_call = {"stock": stock, "analysis": analysis}
        return {
            "stock": stock,
            "profile": {
                "stance": "positive",
                "stance_label": "结构可看",
                "headline": "结构偏多，轮动可看，容量中等，风险可控。",
                "conclusion": "结构有点，先看环境确认。",
            },
            "mx_summary": {"status": "ok", "data": {"cards": []}},
            "news": {"status": "ok", "items": []},
            "market_scan": {"status": "ok", "cards": []},
        }


@unittest.skipIf(create_app is None, "Flask 未安装，跳过 API 测试。")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.fake_mx = FakeMxClient()
        self.fake_profile = FakeProfileClient()
        self.app = create_app(data_client=self.fake, mx_client=self.fake_mx, profile_client=self.fake_profile).test_client()

    def test_search_supports_fuzzy_name(self):
        response = self.app.get("/api/stocks/search?q=平安")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["items"][0]["ts_code"], "000001.SZ")

    def test_analysis_maps_level_and_dates(self):
        response = self.app.get(
            "/api/analysis?ts_code=000001&level=weekly&start_date=2024-01-01&end_date=2024-02-01"
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["stock"]["name"], "平安银行")
        self.assertEqual(data["query"]["level"], "weekly")
        self.assertEqual(self.fake.last_call["start_date"], "20240101")
        self.assertIn("strokes", data)
        self.assertIn("segments", data)
        self.assertIn("trend", data)
        self.assertIn("level_context", data)
        self.assertEqual([item["level"] for item in data["level_context"]["items"]], ["monthly", "weekly"])
        self.assertEqual(len(data["indicators"]["macd"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["bbi"]), len(data["klines"]))

    def test_analysis_maps_intraday_context(self):
        response = self.app.get(
            "/api/analysis?ts_code=000001&level=min60&start_date=2024-01-01&end_date=2024-02-01"
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["query"]["level"], "min60")
        self.assertEqual([item["level"] for item in data["level_context"]["items"]], ["monthly", "weekly", "daily", "min60"])
        self.assertEqual(self.fake.last_call["level"], "min60")

    def test_analysis_rejects_bad_level(self):
        response = self.app.get("/api/analysis?ts_code=000001&level=yearly")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_analysis_returns_not_found(self):
        response = self.app.get("/api/analysis?ts_code=NOPE&level=daily")

        self.assertEqual(response.status_code, 404)
        self.assertIn("未找到股票", response.get_json()["error"]["message"])

    def test_mx_summary_uses_server_side_provider(self):
        response = self.app.get("/api/mx/summary?ts_code=000001.SZ&name=平安银行")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_mx.last_call["ts_code"], "000001.SZ")
        self.assertEqual(data["source"], "mx-data")
        self.assertEqual(data["cards"][0]["key"], "quote")
        self.assertNotIn("MX_APIKEY", str(data))

    def test_mx_summary_requires_stock(self):
        response = self.app.get("/api/mx/summary")

        self.assertEqual(response.status_code, 400)
        self.assertIn("请输入股票", response.get_json()["error"]["message"])

    def test_mx_summary_returns_missing_key_error(self):
        missing_key_mx = MXDataProvider(api_key="fake")
        missing_key_mx.api_key = ""
        app = create_app(data_client=self.fake, mx_client=missing_key_mx).test_client()

        response = app.get("/api/mx/summary?ts_code=000001.SZ&name=平安银行")

        self.assertEqual(response.status_code, 500)
        self.assertIn("MX_APIKEY", response.get_json()["error"]["message"])

    def test_trading_profile_builds_from_posted_stock_and_analysis(self):
        response = self.app.post(
            "/api/trading-profile",
            json={
                "stock": {"ts_code": "000001.SZ", "name": "平安银行", "symbol": "000001"},
                "analysis": {"trend": {"label": "上涨趋势"}},
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_profile.last_call["stock"]["name"], "平安银行")
        self.assertEqual(data["profile"]["stance_label"], "结构可看")

    def test_trading_profile_requires_stock(self):
        response = self.app.post("/api/trading-profile", json={"analysis": {}})

        self.assertEqual(response.status_code, 400)
        self.assertIn("缺少股票信息", response.get_json()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
