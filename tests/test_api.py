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


class FakePickerClient:
    def __init__(self):
        self.last_screen = None
        self.last_candidate = None
        self.last_watchlist_action = None

    def overview(self):
        return {
            "status": "ok",
            "stage": {"label": "主流活跃", "tone": "positive", "summary": "高涨幅个股 88 只。"},
            "universe": {"label": "全A股", "status": "ok", "total": 5000},
            "market_cards": [],
            "news": {"status": "ok", "items": []},
        }

    def screen(self, query_text="", level="daily", limit=6):
        self.last_screen = {"query_text": query_text, "level": level, "limit": limit}
        return {
            "status": "ok",
            "query_text": query_text,
            "level": level,
            "level_label": "日线",
            "universe": {"label": "全A股", "status": "ok", "total": 5000},
            "total": 1,
            "description": "测试条件",
            "parser_text": "",
            "stage": {"label": "主流活跃", "tone": "positive"},
            "candidates": [
                {
                    "stock": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行"},
                    "quote": {"latest_price": "10.0", "change_pct": "2.0%", "change_pct_value": 2.0, "turnover_value": 4.2, "amount_value": 1200000000},
                    "structure": {"label": "结构可看", "tone": "positive", "signal": "买3 候选", "score": 78},
                    "emotion": {"label": "主流活跃", "tone": "positive", "summary": "高涨幅个股 88 只", "score": 74},
                    "capacity": {"label": "容量中等", "tone": "neutral", "summary": "成交额 12 亿", "score": 61},
                    "overall": {"label": "重点观察", "tone": "positive", "decision": "可观察", "score": 73},
                    "screen_row": {"股票代码": "000001", "股票简称": "平安银行"},
                }
            ],
            "errors": [],
        }

    def candidate_detail(self, stock=None, level="daily"):
        self.last_candidate = {"stock": stock, "level": level}
        return {
            "status": "ok",
            "stock": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行"},
            "analysis": {"trend": {"label": "上涨趋势"}, "signals": [], "divergences": [], "risk_cards": []},
            "profile": {
                "profile": {"stance": "neutral", "stance_label": "候选观察", "headline": "结构可看", "conclusion": "先观察。"},
                "mx_summary": {"status": "ok", "data": {"cards": []}},
                "news": {"status": "ok", "items": []},
                "market_scan": {"status": "ok", "cards": []},
            },
            "watchlist": {"status": "ok", "in_watchlist": False, "total": 2},
        }

    def watchlist(self):
        return {
            "status": "ok",
            "items": [{"code": "000001", "name": "平安银行"}],
            "total": 1,
        }

    def manage_watchlist(self, action="", target=""):
        self.last_watchlist_action = {"action": action, "target": target}
        return {"status": "ok", "action": action, "target": target, "message": "操作成功"}


class FakeAIClient:
    def __init__(self):
        self.last_call = None

    def explain(self, stock, analysis, profile_payload):
        self.last_call = {"stock": stock, "analysis": analysis, "profile_payload": profile_payload}
        return {
            "status": "ok",
            "model": "Claude Sonnet 4.6",
            "facts": {"stock": stock},
            "analysis": {
                "summary": "结构有点，但环境和容量还需要确认。",
                "overall_verdict": "候选观察",
                "buy_judgement": "先观察，不急着追价。",
                "confidence": "中",
                "chan_view": {
                    "verdict": "候选观察",
                    "buyable": "买点还没完全确认。",
                    "reason": "结构在演化中。",
                    "basis": ["日线买点仍需确认"],
                    "conditions": ["站稳失效价之上"],
                },
                "yangjia_view": {
                    "verdict": "轮动平衡",
                    "buyable": "情绪一般，只能挑强。",
                    "reason": "赚钱效应尚可。",
                    "basis": ["活跃成交股较多"],
                    "conditions": ["主流继续活跃"],
                },
                "zhang_view": {
                    "verdict": "容量中等",
                    "buyable": "可以跟踪，别重仓。",
                    "reason": "流动性尚可。",
                    "basis": ["成交额充足"],
                    "conditions": ["主力净流继续改善"],
                },
                "risks": ["跌破失效价则撤销假设"],
                "watch_points": ["观察是否放量离开中枢"],
            },
        }


@unittest.skipIf(create_app is None, "Flask 未安装，跳过 API 测试。")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.fake_mx = FakeMxClient()
        self.fake_profile = FakeProfileClient()
        self.fake_picker = FakePickerClient()
        self.fake_ai = FakeAIClient()
        self.app = create_app(
            data_client=self.fake,
            mx_client=self.fake_mx,
            profile_client=self.fake_profile,
            picker_client=self.fake_picker,
            ai_client=self.fake_ai,
        ).test_client()

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

    def test_smart_picker_overview(self):
        response = self.app.get("/api/smart-picker/overview")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["stage"]["label"], "主流活跃")

    def test_smart_picker_screen(self):
        response = self.app.post(
            "/api/smart-picker/screen",
            json={"query_text": "银行股涨幅大于2%", "level": "daily", "limit": 4},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_screen["query_text"], "银行股涨幅大于2%")
        self.assertEqual(self.fake_picker.last_screen["limit"], 4)
        self.assertEqual(data["candidates"][0]["overall"]["label"], "重点观察")

    def test_smart_picker_candidate_detail(self):
        response = self.app.post(
            "/api/smart-picker/candidate",
            json={"stock": {"ts_code": "000001.SZ", "name": "平安银行"}, "level": "weekly"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_candidate["level"], "weekly")
        self.assertEqual(data["stock"]["name"], "平安银行")

    def test_smart_picker_watchlist(self):
        response = self.app.get("/api/smart-picker/watchlist")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["items"][0]["code"], "000001")

    def test_smart_picker_watchlist_manage(self):
        response = self.app.post(
            "/api/smart-picker/watchlist",
            json={"action": "add", "target": "平安银行"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_watchlist_action["action"], "add")
        self.assertEqual(data["status"], "ok")

    def test_smart_picker_ai_brief(self):
        response = self.app.post(
            "/api/smart-picker/ai-brief",
            json={
                "stock": {"ts_code": "000001.SZ", "name": "平安银行", "symbol": "000001"},
                "analysis": {"trend": {"label": "上涨趋势"}},
                "profile": {"profile": {"stance_label": "候选观察"}},
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_ai.last_call["stock"]["name"], "平安银行")
        self.assertEqual(data["analysis"]["overall_verdict"], "候选观察")


if __name__ == "__main__":
    unittest.main()
