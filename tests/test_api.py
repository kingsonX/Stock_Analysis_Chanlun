import unittest
from importlib.util import find_spec

from chanlun_app.data_provider import DataProviderError, StockRecord

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
        return sample_klines()


@unittest.skipIf(create_app is None, "Flask 未安装，跳过 API 测试。")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.app = create_app(data_client=self.fake).test_client()

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
        self.assertEqual(len(data["indicators"]["macd"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["bbi"]), len(data["klines"]))

    def test_analysis_rejects_bad_level(self):
        response = self.app.get("/api/analysis?ts_code=000001&level=yearly")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_analysis_returns_not_found(self):
        response = self.app.get("/api/analysis?ts_code=NOPE&level=daily")

        self.assertEqual(response.status_code, 404)
        self.assertIn("未找到股票", response.get_json()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
