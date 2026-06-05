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
        self.board_last_search = None
        self.board_last_members = None
        self.last_stock_basic_cache = None

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

    def search_boards(self, source, query, board_type="", limit=20):
        self.board_last_search = {"source": source, "query": query, "board_type": board_type, "limit": limit}
        return [
            {
                "ts_code": "BK0001",
                "name": "小金属概念",
                "source": source,
                "source_label": {"dc": "东方财富", "tdx": "通达信", "ths": "同花顺"}.get(source, "板块"),
                "type_key": board_type or "concept",
                "idx_type": "概念板块",
                "trade_date": "20260513",
                "leading": "西部材料",
            }
        ]

    def get_board_members(self, source, ts_code, trade_date=None, force_refresh=False):
        self.board_last_members = {"source": source, "ts_code": ts_code, "trade_date": trade_date}
        return [{"ts_code": ts_code, "con_code": "000001.SZ", "symbol": "000001", "name": "平安银行"}]

    def get_stock_dc_concepts(self, ts_code, trade_date=None, limit=3):
        return [
            {
                "theme_code": "000057.DC",
                "theme_name": "AI 芯片",
                "trade_date": "20260520",
                "industry": "半导体",
                "reason": "DDR5 与算力链共振",
                "hot_num": "12",
            }
        ]

    def get_stock_bak_basic(self, ts_code, trade_date=None):
        return {
            "trade_date": "20260522",
            "ts_code": ts_code,
            "area": "深圳",
            "industry": "银行",
            "pe": 6.8,
            "pb": 0.62,
            "total_share": 194.06,
            "rev_yoy": 3.2,
            "profit_yoy": 2.4,
            "holder_num": 412345,
        }

    def save_stock_basic_cache(self, stock, bak_basic=None):
        self.last_stock_basic_cache = {"stock": stock, "bak_basic": bak_basic}
        return {
            "status": "ok",
            "message": "股票基础资料已写入 PostgreSQL 缓存。",
            "ts_code": stock.get("ts_code", ""),
            "trade_date": (bak_basic or {}).get("trade_date", ""),
        }


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

    def build(self, stock, analysis, include_mx_summary=True):
        self.last_call = {"stock": stock, "analysis": analysis, "include_mx_summary": include_mx_summary}
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
        self.last_watchlist_screen = None
        self.last_candidate = None
        self.last_watchlist_action = None
        self.last_watchlist_group_action = None
        self.last_batch_watchlist = None

    def overview(self):
        return {
            "status": "ok",
            "stage": {"label": "主流活跃", "tone": "positive", "cycle": "主升试错期", "summary": "高涨幅个股 88 只。"},
            "universe": {"label": "全A股", "status": "ok", "total": 5000},
            "market_cards": [],
            "theme_ladders": [],
            "leader_board": [],
            "news": {"status": "ok", "items": []},
        }

    def screen(self, query_text="", level="daily", limit=6):
        return self.screen_with_scopes(query_text=query_text, level=level, limit=limit, board_filters=None)

    def screen_with_board(self, query_text="", level="daily", limit=6, board_filter=None):
        return self.screen_with_scopes(
            query_text=query_text,
            level=level,
            limit=limit,
            board_filters=[board_filter] if board_filter else None,
        )

    def screen_with_scopes(self, query_text="", level="daily", limit=6, board_filters=None):
        self.last_screen = {"query_text": query_text, "level": level, "limit": limit, "board_filters": board_filters or []}
        return {
            "status": "ok",
            "query_text": query_text,
            "level": level,
            "level_label": "日线",
            "universe": {"label": "全A股", "status": "ok", "total": 5000},
            "total": 1,
            "description": "测试条件",
            "parser_text": "",
            "stage": {"label": "主流活跃", "tone": "positive", "cycle": "主升试错期"},
            "theme_ladders": [],
            "leader_board": [],
            "board_filter": (board_filters or [None])[0],
            "board_filters": board_filters or [],
            "candidates": [
                {
                    "stock": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行"},
                    "quote": {"latest_price": "10.0", "change_pct": "2.0%", "change_pct_value": 2.0, "turnover_value": 4.2, "amount_value": 1200000000},
                    "structure": {"label": "结构可看", "tone": "positive", "signal": "买3 候选", "score": 78},
                    "emotion": {"label": "主流热点", "tone": "positive", "summary": "银行是当前主流之一", "score": 74},
                    "leader": {"label": "龙头候选", "tone": "positive", "summary": "银行样本中辨识度居前", "score": 84},
                    "capacity": {"label": "容量中等", "tone": "neutral", "summary": "成交额 12 亿", "score": 61},
                    "overall": {"label": "重点观察", "tone": "positive", "decision": "可观察", "score": 73},
                    "screen_row": {"股票代码": "000001", "股票简称": "平安银行"},
                }
            ],
            "errors": [],
        }

    def screen_watchlist(self, level="daily", limit=None):
        self.last_watchlist_screen = {"level": level, "limit": limit}
        payload = self.screen_with_scopes(query_text="", level=level, limit=limit or 6, board_filters=None)
        payload["source_type"] = "watchlist"
        payload["description"] = "已把东方财富自选股同步为候选池。"
        payload["watchlist"] = {"status": "ok", "label": "我的自选", "total": 1}
        return payload

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
            "execution": {
                "plan": {"title": "交易计划", "verdict": "候选观察"},
                "discipline": {"title": "纪律引擎", "label": "轻仓试错"},
                "review": {"title": "复盘系统", "label": "样本不足"},
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

    def manage_watchlist_group(self, action="", target="", group_name=""):
        self.last_watchlist_group_action = {"action": action, "target": target, "group_name": group_name}
        return {"status": "ok", "action": action, "target": target, "group_name": group_name, "message": "分组操作成功"}

    def batch_manage_watchlist(self, action="", targets_text="", group_name=""):
        self.last_batch_watchlist = {"action": action, "targets_text": targets_text, "group_name": group_name}
        return {
            "status": "ok",
            "action": action,
            "group_name": group_name,
            "total": 2,
            "success_count": 2,
            "fail_count": 0,
            "results": [
                {"target": "平安银行", "status": "ok", "message": "操作成功"},
                {"target": "京东方A", "status": "ok", "message": "操作成功"},
            ],
            "message": "批量操作完成。",
        }


class FakeAIClient:
    def __init__(self):
        self.last_call = None

    def explain(self, stock, analysis, profile_payload):
        self.last_call = {"stock": stock, "analysis": analysis, "profile_payload": profile_payload}
        return {
            "status": "ok",
            "provider": "火山方舟",
            "model": "doubao-seed-2-0-lite",
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


class FakeReviewClient:
    def __init__(self):
        self.last_trade_date = None
        self.last_ai_payload = None

    def overview(self, trade_date=None):
        self.last_trade_date = trade_date
        return {
            "status": "ok",
            "trade_date": trade_date or "20260515",
            "summary": {
                "dragon_count": 12,
                "hot_money_count": 8,
                "up_limit_count": 66,
                "down_limit_count": 5,
                "burst_count": 14,
                "highest_board": 5,
                "focus_board_count": 3,
                "focus_stock_count": 4,
            },
            "hot_money_stats": {
                "record_count": 8,
                "merged_count": 1,
            },
            "dragon_tiger": [{"ts_code": "000001.SZ", "name": "平安银行", "net_amount": 420000000.0, "reason": "日涨幅偏离值达7%"}],
            "hot_money_trades": [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "hm_name": "北京帮",
                    "hot_money_label": "北京帮",
                    "exalter": "中国中金财富证券有限公司北京宋庄路证券营业部",
                    "buy_amount": 260000000.0,
                    "sell_amount": 80000000.0,
                    "net_amount": 180000000.0,
                    "org_count": 1,
                    "record_count": 8,
                    "tag": "净买入",
                }
            ],
            "limit_lists": {
                "up": [{"ts_code": "000001.SZ", "name": "平安银行", "limit_times": 2, "strth": 98.0}],
                "down": [],
                "burst": [],
                "other": [],
            },
            "ladder": [{"ts_code": "000001.SZ", "name": "平安银行", "continue_num": 3, "limit_times": 3}],
            "focus_boards": [{"name": "银行概念", "rank": 1, "limit_count": 6, "watch_reason": "涨停家数 6。"}],
            "focus_stocks": [{"ts_code": "000001.SZ", "name": "平安银行", "score": 26.0, "verdict": "重点盯"}],
            "notes": {
                "summary": "今天最强先看银行概念。",
                "watch_points": ["先看银行概念能否继续扩散。"],
                "risk_points": ["若炸板增多，先回防守。"],
            },
            "ai_review": {"status": "idle", "message": ""},
        }

    def explain_overview(self, review_payload):
        self.last_ai_payload = review_payload
        payload = dict(review_payload)
        payload["ai_review"] = {
            "status": "ok",
            "provider": "火山方舟",
            "model": "doubao-seed-2-0-lite",
            "analysis": {
                "summary": "金融线更强，先看前排承接。",
                "market_stage": "主流试错",
                "watch_points": ["先看银行概念前排"],
                "risk_points": ["若炸板扩散先防守"],
            },
        }
        return payload


class FakeWatchtowerStore:
    def __init__(self):
        self.deleted = []

    def delete_entry(self, ts_code):
        self.deleted.append(ts_code)
        return True


class FakeWatchtowerClient:
    def __init__(self):
        self.last_overview = None
        self.last_delete = None
        self.last_realtime = None
        self.last_track = None
        self.last_eastmoney_add = None
        self.store = FakeWatchtowerStore()

    def overview(self, query="", page=1, page_size=12):
        self.last_overview = {"query": query, "page": page, "page_size": page_size}
        return {
            "status": "ok",
            "query": query,
            "page": page,
            "page_size": page_size,
            "total": 1,
            "total_pages": 1,
            "summary": {
                "total": 1,
                "strong_count": 1,
                "absorb_count": 0,
                "risk_count": 0,
                "headline": "今天先盯强承接和主流先手。",
                "action": "先盯强票。",
                "realtime_error": "",
            },
            "items": [
                {
                    "stock": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "industry": "银行", "area": "深圳", "market": "主板"},
                    "cache": {"trade_date": "20260525", "pe": 3.57, "pb": 0.45, "holder_num": 457610, "total_share": 194.06, "rev_yoy": 4.7, "profit_yoy": 3.0},
                    "realtime": {"close": 11.23, "day_pct": 1.82, "open_pct": 0.42, "amplitude_pct": 2.16, "trade_time": "14:56:22"},
                    "yangjia": {"label": "主流先手", "tone": "positive", "action": "先盯前排，不追后排。", "summary": "强于昨收。"},
                }
            ],
            "realtime_error": "",
        }

    def delete_stock(self, ts_code=""):
        self.last_delete = ts_code
        return {
            "status": "ok",
            "deleted": True,
            "stock": {"ts_code": ts_code, "name": "平安银行"},
            "message": "已删除",
        }

    def realtime_detail(self, ts_code=""):
        self.last_realtime = ts_code
        return {
            "status": "ok",
            "stock": {"ts_code": ts_code, "symbol": "000001", "name": "平安银行", "industry": "银行"},
            "cache": {"trade_date": "20260525", "holder_num": 457610},
            "realtime": {"pre_close": 11.03, "open": 11.08, "high": 11.28, "low": 11.02, "close": 11.23, "day_pct": 1.82},
            "yangjia": {"label": "主流先手", "tone": "positive", "action": "先盯前排，不追后排。", "summary": "强于昨收。"},
            "realtime_error": "",
        }

    def track_stock(self, stock=None, bak_basic=None):
        self.last_track = {"stock": stock, "bak_basic": bak_basic}
        return {"status": "ok", "message": "智能盯盘数据库已更新。"}

    def add_to_eastmoney_group(self, ts_code=""):
        self.last_eastmoney_add = ts_code
        return {
            "status": "ok",
            "group_name": "重点监控",
            "stock": {"ts_code": ts_code, "name": "平安银行"},
            "message": "平安银行 已加入东方财富自选组“重点监控”。",
        }


@unittest.skipIf(create_app is None, "Flask 未安装，跳过 API 测试。")
class ApiTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.fake_mx = FakeMxClient()
        self.fake_profile = FakeProfileClient()
        self.fake_picker = FakePickerClient()
        self.fake_ai = FakeAIClient()
        self.fake_review = FakeReviewClient()
        self.fake_watchtower = FakeWatchtowerClient()
        self.app = create_app(
            data_client=self.fake,
            mx_client=self.fake_mx,
            profile_client=self.fake_profile,
            picker_client=self.fake_picker,
            ai_client=self.fake_ai,
            review_client=self.fake_review,
            watchtower_client=self.fake_watchtower,
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
        self.assertEqual(data["stock"]["dc_concepts"][0]["theme_name"], "AI 芯片")
        self.assertEqual(data["stock"]["bak_basic"]["holder_num"], 412345)
        self.assertEqual(data["query"]["level"], "weekly")
        self.assertEqual(self.fake.last_call["start_date"], "20240101")
        self.assertIn("strokes", data)
        self.assertIn("segments", data)
        self.assertIn("trend", data)
        self.assertIn("level_context", data)
        self.assertIn("ma_centers", data)
        self.assertIn("ma_signals", data)
        self.assertEqual([item["level"] for item in data["level_context"]["items"]], ["monthly", "weekly"])
        self.assertEqual(len(data["indicators"]["macd"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["bbi"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["ma5"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["ma10"]), len(data["klines"]))
        self.assertEqual(len(data["indicators"]["ma20"]), len(data["klines"]))

    def test_board_search_supports_eastmoney_filters(self):
        response = self.app.get("/api/boards/search?q=小金属&type=concept&limit=8")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake.board_last_search["source"], "dc")
        self.assertEqual(self.fake.board_last_search["query"], "小金属")
        self.assertEqual(self.fake.board_last_search["board_type"], "concept")
        self.assertEqual(data["items"][0]["name"], "小金属概念")

    def test_board_search_supports_tdx_source(self):
        response = self.app.get("/api/boards/search?source=tdx&q=稀土&type=concept&limit=6")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fake.board_last_search["source"], "tdx")
        self.assertEqual(self.fake.board_last_search["query"], "稀土")

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
        self.assertTrue(self.fake_profile.last_call["include_mx_summary"])

    def test_trading_profile_supports_skipping_mx_summary(self):
        response = self.app.post(
            "/api/trading-profile",
            json={
                "stock": {"ts_code": "000001.SZ", "name": "平安银行", "symbol": "000001"},
                "analysis": {"trend": {"label": "上涨趋势"}},
                "include_mx_summary": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.fake_profile.last_call["include_mx_summary"])

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
            json={
                "query_text": "银行股涨幅大于2%",
                "level": "daily",
                "limit": 4,
                "board_ts_code": "BK0001",
                "board_name": "小金属概念",
                "board_type": "concept",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_screen["query_text"], "银行股涨幅大于2%")
        self.assertEqual(self.fake_picker.last_screen["limit"], 4)
        self.assertEqual(self.fake_picker.last_screen["board_filters"][0]["ts_code"], "BK0001")
        self.assertEqual(data["candidates"][0]["overall"]["label"], "重点观察")

    def test_smart_picker_screen_supports_multi_board_sources(self):
        response = self.app.post(
            "/api/smart-picker/screen",
            json={
                "query_text": "",
                "level": "daily",
                "limit": 4,
                "tdx_board_ts_code": "T0001",
                "tdx_board_name": "稀土永磁",
                "tdx_board_type": "concept",
                "ths_board_ts_code": "TH0001",
                "ths_board_name": "固态电池",
                "ths_board_type": "concept",
            },
        )

        self.assertEqual(response.status_code, 200)
        used_sources = [item["source"] for item in self.fake_picker.last_screen["board_filters"] if item.get("name") or item.get("ts_code")]
        self.assertEqual(used_sources, ["tdx", "ths"])

    def test_smart_picker_screen_watchlist_source(self):
        response = self.app.post(
            "/api/smart-picker/screen",
            json={"source_type": "watchlist", "level": "weekly", "limit_all": True},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_watchlist_screen["level"], "weekly")
        self.assertIsNone(self.fake_picker.last_watchlist_screen["limit"])
        self.assertEqual(data["source_type"], "watchlist")

    def test_smart_picker_candidate_detail(self):
        response = self.app.post(
            "/api/smart-picker/candidate",
            json={"stock": {"ts_code": "000001.SZ", "name": "平安银行"}, "level": "weekly"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_candidate["level"], "weekly")
        self.assertEqual(data["stock"]["name"], "平安银行")
        self.assertEqual(data["execution"]["plan"]["title"], "交易计划")

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

    def test_smart_picker_eastmoney_batch_add_group(self):
        response = self.app.post(
            "/api/smart-picker/eastmoney-batch",
            json={"action": "add_group", "group_name": "重点监控", "targets_text": "平安银行\n京东方A"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_batch_watchlist["action"], "add_group")
        self.assertEqual(self.fake_picker.last_batch_watchlist["group_name"], "重点监控")
        self.assertEqual(data["success_count"], 2)

    def test_smart_picker_eastmoney_batch_delete(self):
        response = self.app.post(
            "/api/smart-picker/eastmoney-batch",
            json={"action": "delete", "targets_text": "平安银行\n京东方A"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_batch_watchlist["action"], "delete")
        self.assertEqual(data["status"], "ok")

    def test_analysis_watchlist_manage_and_cache(self):
        response = self.app.post(
            "/api/analysis/watchlist",
            json={
                "action": "add",
                "stock": {
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "name": "平安银行",
                    "bak_basic": {"trade_date": "20260522", "holder_num": 412345},
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_picker.last_watchlist_action["action"], "add")
        self.assertEqual(self.fake.last_stock_basic_cache["stock"]["name"], "平安银行")
        self.assertEqual(self.fake_watchtower.last_track["stock"]["name"], "平安银行")
        self.assertEqual(data["cache"]["status"], "ok")
        self.assertEqual(data["stock"]["ts_code"], "000001.SZ")
        self.assertEqual(data["watchtower"]["status"], "ok")

    def test_watchtower_overview(self):
        response = self.app.get("/api/watchtower/overview?q=平安&page=2&page_size=8")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_watchtower.last_overview["query"], "平安")
        self.assertEqual(self.fake_watchtower.last_overview["page"], 2)
        self.assertEqual(self.fake_watchtower.last_overview["page_size"], 8)
        self.assertEqual(data["items"][0]["yangjia"]["label"], "主流先手")

    def test_watchtower_delete(self):
        response = self.app.post("/api/watchtower/delete", json={"ts_code": "000001.SZ"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fake_watchtower.last_delete, "000001.SZ")
        self.assertTrue(response.get_json()["deleted"])

    def test_watchtower_eastmoney_add(self):
        response = self.app.post("/api/watchtower/eastmoney-add", json={"ts_code": "000001.SZ"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.fake_watchtower.last_eastmoney_add, "000001.SZ")
        self.assertEqual(response.get_json()["group_name"], "重点监控")

    def test_watchtower_realtime(self):
        response = self.app.get("/api/watchtower/realtime?ts_code=000001.SZ")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(self.fake_watchtower.last_realtime, "000001.SZ")
        self.assertEqual(data["stock"]["name"], "平安银行")

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

    def test_review_overview(self):
        response = self.app.get("/api/review/overview?trade_date=2026-05-15")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["summary"]["dragon_count"], 12)
        self.assertEqual(data["focus_boards"][0]["name"], "银行概念")
        self.assertEqual(data["ai_review"]["status"], "idle")
        self.assertEqual(self.fake_review.last_trade_date, "20260515")

    def test_review_ai_brief(self):
        response = self.app.post(
            "/api/review/ai-brief",
            json={
                "review": {
                    "status": "ok",
                    "trade_date": "20260515",
                    "focus_boards": [{"name": "银行概念"}],
                    "focus_stocks": [{"ts_code": "000001.SZ", "name": "平安银行"}],
                    "notes": {"summary": "今天最强先看银行概念。"},
                }
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ai_review"]["status"], "ok")
        self.assertEqual(self.fake_review.last_ai_payload["trade_date"], "20260515")


if __name__ == "__main__":
    unittest.main()
