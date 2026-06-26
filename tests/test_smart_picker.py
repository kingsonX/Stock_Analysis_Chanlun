import unittest

import pandas as pd

from chanlun_app.smart_picker import (
    MXWatchlistProvider,
    SmartPickerService,
    _candidate_capacity,
    _candidate_emotion,
    _candidate_leader,
    _candidate_structure,
)
from chanlun_app.data_provider import DataProviderError
from chanlun_app.mx_provider import MXProviderError


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
        self.boards = [
            {
                "ts_code": "BK0001",
                "name": "银行概念",
                "source": "dc",
                "source_label": "东方财富",
                "type_key": "concept",
                "idx_type": "概念板块",
                "trade_date": "20260513",
                "leading": "平安银行",
            },
            {
                "ts_code": "BK0002",
                "name": "证券行业",
                "source": "dc",
                "source_label": "东方财富",
                "type_key": "industry",
                "idx_type": "行业板块",
                "trade_date": "20260513",
                "leading": "东方财富",
            },
            {
                "ts_code": "T0001",
                "name": "稀土永磁",
                "source": "tdx",
                "source_label": "通达信",
                "type_key": "concept",
                "idx_type": "概念板块",
                "trade_date": "20260513",
                "leading": "西部材料",
            },
            {
                "ts_code": "TH0001",
                "name": "固态电池",
                "source": "ths",
                "source_label": "同花顺",
                "type_key": "concept",
                "idx_type": "概念题材",
                "trade_date": "20260513",
                "leading": "东方财富",
            },
        ]
        self.board_members = {
            "BK0001": [
                {"ts_code": "BK0001", "con_code": "000001.SZ", "symbol": "000001", "name": "平安银行"},
                {"ts_code": "BK0001", "con_code": "600000.SH", "symbol": "600000", "name": "浦发银行"},
            ],
            "BK0002": [
                {"ts_code": "BK0002", "con_code": "300059.SZ", "symbol": "300059", "name": "东方财富"},
            ],
            "T0001": [
                {"ts_code": "T0001", "con_code": "300059.SZ", "symbol": "300059", "name": "东方财富"},
            ],
            "TH0001": [
                {"ts_code": "TH0001", "con_code": "300059.SZ", "symbol": "300059", "name": "东方财富"},
            ],
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

    def search_boards(self, source, query, board_type="", limit=20):
        items = [
            item for item in self.boards if item["source"] == source and (query in item["name"] or query.upper() in item["ts_code"].upper())
        ]
        if board_type:
            items = [item for item in items if item["type_key"] == board_type]
        return items[:limit]

    def get_board_members(self, source, ts_code, trade_date=None, force_refresh=False):
        return self.board_members.get(ts_code, [])

    def get_realtime_daily(self, ts_codes):
        if isinstance(ts_codes, str):
            codes = [item.strip().upper() for item in ts_codes.split(",") if item.strip()]
        else:
            codes = [str(item or "").strip().upper() for item in ts_codes if str(item or "").strip()]
        rows = {
            "000001.SZ": {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "pre_close": 10.0,
                "close": 11.0,
                "vol": 920000000,
                "amount": 1600000000,
            },
            "600000.SH": {
                "ts_code": "600000.SH",
                "name": "浦发银行",
                "pre_close": 9.0,
                "close": 9.61,
                "vol": 410000000,
                "amount": 1100000000,
            },
            "300059.SZ": {
                "ts_code": "300059.SZ",
                "name": "东方财富",
                "pre_close": 17.39,
                "close": 18.36,
                "vol": 310000000,
                "amount": 1260000000,
            },
        }
        return [rows[code] for code in codes if code in rows]

    def get_stock_bak_basic(self, ts_code, trade_date=None):
        rows = {
            "000001.SZ": {"ts_code": "000001.SZ", "total_share": 194.06, "float_share": 194.06},
            "600000.SH": {"ts_code": "600000.SH", "total_share": 293.52, "float_share": 293.52},
            "300059.SZ": {"ts_code": "300059.SZ", "total_share": 66.5, "float_share": 50.0},
        }
        return rows.get(str(ts_code or "").strip().upper(), {})


class TokenlessKlineDataClient(FakeDataClient):
    def get_klines(self, ts_code, level, start_date, end_date):
        raise DataProviderError("缺少 TUSHARE_TOKEN 环境变量，请先配置 Tushare Pro Token。", 500)


class MissingStockDataClient(TokenlessKlineDataClient):
    def resolve_stock(self, query):
        raise DataProviderError("缺少 TUSHARE_TOKEN 环境变量，请先配置 Tushare Pro Token。", 500)


class SparseThemeDataClient(FakeDataClient):
    def __init__(self):
        super().__init__()
        extra_records = [
            FakeStock(symbol="300001", name="易事特", ts_code="300001.SZ", industry="电气设备"),
            FakeStock(symbol="300002", name="节能铁汉", ts_code="300002.SZ", industry="电气设备"),
            FakeStock(symbol="300003", name="丰光精密", ts_code="300003.SZ", industry="电气设备"),
            FakeStock(symbol="300004", name="金雷股份", ts_code="300004.SZ", industry="电气设备"),
        ]
        for stock in extra_records:
            self.records[stock.symbol] = stock
            self.records[stock.ts_code] = stock
            self.records[stock.name] = stock


class BullishKlineDataClient(FakeDataClient):
    def get_klines(self, ts_code, level, start_date, end_date):
        rows = []
        for idx in range(36):
            close = 10 + idx * 0.35
            rows.append(
                {
                    "index": idx,
                    "date": f"202402{idx + 1:02d}",
                    "open": close - 0.18,
                    "high": close + 0.32,
                    "low": close - 0.35,
                    "close": close,
                    "vol": 1000 + idx * 20,
                    "amount": 10000 + idx * 100,
                }
            )
        return rows


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
                    "总市值": "2000亿",
                },
                {
                    "股票代码": "600000",
                    "股票简称": "浦发银行",
                    "最新价": "9.88",
                    "涨跌幅": "6.8%",
                    "成交额": "11.0亿",
                    "换手率": "4.3%",
                    "总市值": "1500亿",
                },
                {
                    "股票代码": "300059",
                    "股票简称": "东方财富",
                    "最新价": "18.36",
                    "涨跌幅": "5.6%",
                    "成交额": "12.6亿",
                    "换手率": "6.2%",
                    "总市值": "500亿",
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
        return {
            "status": "ok",
            "items": [
                {
                    "code": "000001",
                    "name": "平安银行",
                    "latest_price": "10.22",
                    "change_pct": "2.0%",
                    "turnover": "5.6%",
                    "raw": {"成交额": "16.0亿"},
                }
            ],
            "total": 1,
        }

    def manage(self, action="", target=""):
        self.last_manage = {"action": action, "target": target}
        return {"status": "ok", "action": action, "target": target, "message": "操作成功"}


class ScriptedGroupWatchlistProvider(MXWatchlistProvider):
    def __init__(self, scripted_results):
        super().__init__(api_key="fake")
        self.scripted_results = list(scripted_results)
        self.queries = []

    def _post_json(self, url, payload):
        self.queries.append(payload.get("query", ""))
        if not self.scripted_results:
            raise AssertionError("缺少脚本化返回结果。")
        result = self.scripted_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


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
        self.assertEqual(result["leader_board"][0]["role"], "龙头候选")

    def test_screen_filters_market_turnover_and_market_cap(self):
        result = self.service.screen(
            query_text="银行股涨幅大于2%",
            level="daily",
            limit=4,
            screen_filters={
                "market_scope": "chinext",
                "turnover_min": 6,
                "market_cap_max": 800,
            },
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["candidates"][0]["stock"]["symbol"], "300059")
        self.assertEqual(result["filters"]["market_scope"], "chinext")

    def test_screen_technical_shape_filter_uses_klines(self):
        result = self.service.screen(
            query_text="银行股涨幅大于2%",
            level="daily",
            limit=4,
            screen_filters={"technical_shape": "ma_bullish"},
        )
        self.assertEqual(result["candidates"], [])

        bullish_service = SmartPickerService(
            data_client=BullishKlineDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )
        bullish_result = bullish_service.screen(
            query_text="银行股涨幅大于2%",
            level="daily",
            limit=4,
            screen_filters={"technical_shape": "ma_bullish"},
        )
        self.assertTrue(bullish_result["candidates"])
        self.assertEqual(bullish_result["candidates"][0]["technical_shape"]["label"], "均线多头排列")

    def test_leader_label_requires_theme_depth_and_takeover(self):
        service = SmartPickerService(
            data_client=SparseThemeDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )
        rows = [
            {"股票代码": "300001", "股票简称": "易事特", "涨跌幅": "20.0%", "成交额": "9.2亿", "换手率": "19.0%"},
            {"股票代码": "300002", "股票简称": "节能铁汉", "涨跌幅": "19.8%", "成交额": "0.8亿", "换手率": "22.6%"},
            {"股票代码": "300003", "股票简称": "丰光精密", "涨跌幅": "29.9%", "成交额": "0.4亿", "换手率": "19.2%"},
            {"股票代码": "300004", "股票简称": "金雷股份", "涨跌幅": "11.0%", "成交额": "0.7亿", "换手率": "8.5%"},
        ]

        theme_context = service._build_theme_context(rows)
        stock = service.data_client.resolve_stock("300003.SZ").as_dict()
        leader = _candidate_leader(stock, rows[2], theme_context)

        self.assertEqual(theme_context["groups"][0]["active_count"], 0)
        self.assertEqual(leader["label"], "前排助攻")
        self.assertIn("主流合力或承接确认还不够", leader["summary"])
        self.assertEqual(theme_context["leaders"][0]["role"], "前排助攻")

    def test_candidate_structure_rejects_buy_signal_in_downtrend(self):
        analysis = {
            "trend": {
                "type": "趋势",
                "direction": "down",
                "label": "下跌趋势",
                "position": "below_center",
                "position_label": "中枢下方",
            },
            "signals": [
                {
                    "name": "buy3",
                    "side": "buy",
                    "status": "confirmed",
                    "status_label": "确认",
                    "invalidation_price": 18.6,
                }
            ],
            "divergences": [],
        }

        structure = _candidate_structure(analysis, "daily")

        self.assertEqual(structure["label"], "结构回避")
        self.assertEqual(structure["tone"], "caution")

    def test_candidate_structure_caps_unfinished_rebound_to_observe(self):
        analysis = {
            "trend": {
                "type": "未成中枢",
                "direction": "up",
                "label": "线段推进",
                "position": "no_center",
                "position_label": "无中枢",
            },
            "signals": [
                {
                    "name": "buy3",
                    "side": "buy",
                    "status": "confirmed",
                    "status_label": "确认",
                    "invalidation_price": 22.3,
                }
            ],
            "divergences": [],
        }

        structure = _candidate_structure(analysis, "daily")

        self.assertEqual(structure["label"], "候选观察")
        self.assertEqual(structure["tone"], "neutral")

    def test_theme_context_does_not_promote_board_list_without_quote_data(self):
        rows = [
            {"股票代码": "000001", "股票简称": "平安银行"},
            {"股票代码": "600000", "股票简称": "浦发银行"},
        ]

        theme_context = self.service._build_theme_context(rows)
        group = theme_context["groups_by_industry"]["银行"]
        stock = self.service.data_client.resolve_stock("000001.SZ").as_dict()
        emotion = _candidate_emotion(stock, rows[0], theme_context)
        leader = _candidate_leader(stock, rows[0], theme_context)

        self.assertFalse(group["has_market_evidence"])
        self.assertEqual(group["tier_label"], "轮动观察")
        self.assertEqual(emotion["tone"], "caution")
        self.assertEqual(leader["label"], "非核心观察")

    def test_candidate_capacity_requires_amount_evidence(self):
        capacity = _candidate_capacity({"股票代码": "000001", "股票简称": "平安银行"})

        self.assertEqual(capacity["label"], "容量待核")
        self.assertEqual(capacity["tone"], "caution")
        self.assertIn("缺少成交额", capacity["summary"])

    def test_screen_supports_board_scope(self):
        result = self.service.screen_with_board(
            query_text="银行股涨幅大于2%",
            level="daily",
            limit=4,
            board_filter={"name": "证券行业", "board_type": "industry"},
        )

        self.assertEqual(result["board_filters"][0]["name"], "证券行业")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["candidates"][0]["stock"]["symbol"], "300059")

    def test_screen_supports_board_only_query(self):
        result = self.service.screen_with_scopes(
            query_text="",
            level="daily",
            limit=4,
            board_filters=[{"source": "tdx", "name": "稀土永磁", "board_type": "concept"}],
        )

        self.assertEqual(result["board_filters"][0]["source"], "tdx")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["candidates"][0]["stock"]["symbol"], "300059")
        self.assertEqual(result["candidates"][0]["quote"]["amount"], "12.60亿")
        self.assertEqual(result["candidates"][0]["quote"]["turnover"], "6.20%")
        self.assertEqual(result["candidates"][0]["quote"]["market_cap"], "1221亿")
        self.assertIn("总市值 1221亿", result["candidates"][0]["capacity"]["summary"])

    def test_screen_watchlist_builds_candidates(self):
        result = self.service.screen_watchlist(level="daily")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source_type"], "watchlist")
        self.assertEqual(result["watchlist"]["total"], 1)
        self.assertEqual(result["candidates"][0]["stock"]["symbol"], "000001")
        self.assertEqual(result["candidates"][0]["quote"]["amount_value"], 1600000000.0)

    def test_screen_watchlist_degrades_when_structure_data_missing(self):
        service = SmartPickerService(
            data_client=TokenlessKlineDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )

        result = service.screen_watchlist(level="daily")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fallback_count"], 1)
        self.assertEqual(result["candidates"][0]["structure"]["label"], "结构待补充")
        self.assertFalse(result["candidates"][0]["analysis_available"])

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

    def test_manage_group_surfaces_real_create_error(self):
        provider = ScriptedGroupWatchlistProvider(
            [{"requestId": None, "message": "Failure", "status": -1, "code": -1, "data": None}]
        )

        with self.assertRaises(MXProviderError) as ctx:
            provider.manage_group("add", "平安银行", "重点监控")

        self.assertEqual(provider.queries, ["创建自选股组重点监控"])
        self.assertIn("创建东方财富分组失败", ctx.exception.message)
        self.assertIn("message=Failure", ctx.exception.message)
        self.assertIn("status=-1", ctx.exception.message)

    def test_manage_group_reports_unverified_group_write(self):
        provider = ScriptedGroupWatchlistProvider(
            [
                {"requestId": None, "message": "OK", "status": 0, "code": 0, "data": "已创建分组重点监控"},
                {
                    "requestId": None,
                    "message": "OK",
                    "status": 0,
                    "code": 0,
                    "data": "好的，已为您将1个标的（平安银行）添加自选。",
                },
            ]
        )

        with self.assertRaises(MXProviderError) as ctx:
            provider.manage_group("add", "平安银行", "重点监控")

        self.assertEqual(provider.queries, ["创建自选股组重点监控", "把平安银行添加到重点监控自选股组"])
        self.assertIn("未确认写入分组", ctx.exception.message)
        self.assertIn("添加自选", ctx.exception.message)

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

    def test_candidate_detail_degrades_when_structure_data_missing(self):
        service = SmartPickerService(
            data_client=TokenlessKlineDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )

        result = service.candidate_detail(stock={"ts_code": "000001.SZ"}, level="daily")

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["analysis"]["unavailable"])
        self.assertIn("缺少 TUSHARE_TOKEN", result["analysis"]["message"])
        self.assertEqual(result["execution"]["plan"]["setup"], "数据待补充")

    def test_candidate_detail_degrades_when_stock_lookup_missing(self):
        service = SmartPickerService(
            data_client=MissingStockDataClient(),
            mx_data_provider=None,
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            watchlist_provider=self.watchlist,
            trading_profile=FakeProfileService(),
        )

        result = service.candidate_detail(stock={"symbol": "000001", "name": "平安银行"}, level="daily")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stock"]["symbol"], "000001")
        self.assertTrue(result["analysis"]["unavailable"])


if __name__ == "__main__":
    unittest.main()
