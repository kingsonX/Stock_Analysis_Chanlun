import unittest

from chanlun_app.trading_profile import TradingProfileService


class FakeDataProvider:
    def summary(self, ts_code="", name=""):
        return {
            "stock": {"ts_code": ts_code, "name": name},
            "cards": [],
            "quote": {
                "rows": [
                    {
                        "date": "最新",
                        "成交额": "35.2亿",
                        "换手率": "6.8%",
                    }
                ],
                "columns": ["date", "成交额", "换手率"],
            },
            "valuation": {
                "rows": [{"date": "最新", "总市值": "420亿"}],
                "columns": ["date", "总市值"],
            },
            "fund_flow": {
                "rows": [{"date": "最新", "主力净流入": "1.8亿"}],
                "columns": ["date", "主力净流入"],
            },
        }


class FakeNewsProvider:
    def digest(self, target=""):
        return {
            "status": "ok",
            "items": [
                {
                    "title": f"{target} 最新公告：签订新订单",
                    "date": "20260503",
                    "source": "测试源",
                    "type": "公告",
                    "summary": "订单金额提升，暂无负面监管词。",
                }
            ],
        }


class FakeScreenProvider:
    def scan(self, stock_name="", industry="", symbol=""):
        return {
            "status": "ok",
            "industry": industry,
            "cards": [
                {"key": "market_heat", "label": "市场热度", "status": "ok", "total": 88, "rows": [], "hit_current_stock": False},
                {"key": "market_liquidity", "label": "成交活跃", "status": "ok", "total": 136, "rows": [], "hit_current_stock": False},
                {"key": "industry_strength", "label": "行业强度", "status": "ok", "total": 12, "rows": [{"股票代码": symbol, "股票简称": stock_name}], "hit_current_stock": True},
            ],
        }


class TradingProfileTest(unittest.TestCase):
    def test_profile_combines_structure_emotion_capacity(self):
        service = TradingProfileService(
            mx_data_provider=FakeDataProvider(),
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
        )
        stock = {"ts_code": "000001.SZ", "name": "平安银行", "symbol": "000001", "industry": "银行"}
        analysis = {
            "query": {"level_label": "日线"},
            "trend": {
                "label": "上涨趋势",
                "direction": "up",
                "position": "above_center",
                "position_label": "中枢上方",
                "reason": "最近两个中枢重心上移。",
            },
            "signals": [
                {
                    "type": "三类买点",
                    "side": "buy",
                    "status": "candidate",
                    "status_label": "候选",
                    "invalidation_price": 9.5,
                }
            ],
            "divergences": [{"label": "趋势背驰"}],
        }

        result = service.build(stock=stock, analysis=analysis)

        self.assertEqual(result["profile"]["stance"], "neutral")
        self.assertIn("结构偏多", result["profile"]["headline"])
        self.assertIn("是否值得买", result["profile"]["decision"])
        self.assertEqual(result["profile"]["emotion"]["label"], "主流活跃")
        self.assertEqual(result["profile"]["emotion"]["title"], "养家视角")
        self.assertEqual(result["profile"]["capacity"]["label"], "容量充足")
        self.assertEqual(result["profile"]["capacity"]["title"], "章盟主视角")
        self.assertEqual(result["profile"]["risk"]["label"], "风险需盯")
        self.assertTrue(result["profile"]["structure"]["basis"])
        self.assertIn("是否值得买", result["profile"]["structure"]["action"])

    def test_profile_degrades_when_external_source_errors(self):
        class BrokenNewsProvider:
            def digest(self, target=""):
                return {"status": "error", "message": "资讯不可用"}

        class BrokenScreenProvider:
            def scan(self, stock_name="", industry="", symbol=""):
                return {"status": "error", "message": "扫描失败", "cards": []}

        service = TradingProfileService(
            mx_data_provider=FakeDataProvider(),
            news_provider=BrokenNewsProvider(),
            screen_provider=BrokenScreenProvider(),
        )
        result = service.build(
            stock={"ts_code": "000001.SZ", "name": "平安银行", "symbol": "000001", "industry": "银行"},
            analysis={"trend": {"label": "结构不足", "direction": "", "position": "no_center", "reason": "暂无清晰结构。"}, "signals": [], "divergences": []},
        )

        self.assertEqual(result["profile"]["stance"], "neutral")
        self.assertEqual(result["news"]["status"], "error")
        self.assertEqual(result["market_scan"]["status"], "error")
        self.assertIn("是否值得买", result["profile"]["decision"])


if __name__ == "__main__":
    unittest.main()
