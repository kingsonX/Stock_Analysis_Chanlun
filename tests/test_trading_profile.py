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


class FakeAIExplainer:
    def explain(self, stock=None, analysis=None, profile_payload=None):
        return {
            "status": "ok",
            "provider": "DeepSeek",
            "model": "deepseek-v4-pro",
            "analysis": {
                "summary": "结构、主流和容量可以一起看，但执行仍要等确认。",
                "overall_verdict": "候选观察",
                "buy_judgement": "先跟踪，不急着追高。",
                "confidence": "中",
                "chan_view": {
                    "verdict": "候选观察",
                    "buyable": "买点还要确认",
                    "reason": "结构尚未走到强确认。",
                    "basis": ["仍在中枢上方运行"],
                    "conditions": ["不能跌破失效价"],
                },
                "yangjia_view": {
                    "verdict": "主流活跃",
                    "buyable": "主流里优先看强票",
                    "reason": "赚钱效应仍在。",
                    "basis": ["高涨幅样本仍活跃"],
                    "conditions": ["主流继续扩散"],
                },
                "zhang_view": {
                    "verdict": "容量可跟踪",
                    "buyable": "容量够看，但别重仓",
                    "reason": "流动性仍有承接。",
                    "basis": ["成交额不差"],
                    "conditions": ["继续放量承接"],
                },
                "risks": ["跌回中枢内部要重算假设"],
                "watch_points": ["观察是否放量突破前高"],
            },
        }


class TradingProfileTest(unittest.TestCase):
    def test_profile_service_reuses_external_timeout_for_news_and_scan(self):
        class TimedDataProvider(FakeDataProvider):
            timeout_seconds = 6
            api_key = "fake"

        service = TradingProfileService(mx_data_provider=TimedDataProvider())

        self.assertEqual(service.news_provider.timeout_seconds, 6)
        self.assertEqual(service.screen_provider.timeout_seconds, 6)

    def test_profile_combines_structure_emotion_capacity(self):
        service = TradingProfileService(
            mx_data_provider=FakeDataProvider(),
            news_provider=FakeNewsProvider(),
            screen_provider=FakeScreenProvider(),
            ai_explainer=FakeAIExplainer(),
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
        self.assertEqual(result["profile"]["headline"], "结构、主流和容量可以一起看，但执行仍要等确认。")
        self.assertEqual(result["profile"]["decision"], "先跟踪，不急着追高。")
        self.assertEqual(result["profile"]["stance_label"], "候选观察")
        self.assertEqual(result["profile"]["ai_summary"]["provider"], "DeepSeek")
        self.assertEqual(len(result["profile"]["ai_sections"]), 4)
        self.assertEqual(result["profile"]["emotion"]["label"], "主流活跃")
        self.assertEqual(result["profile"]["emotion"]["title"], "养家视角")
        self.assertEqual(result["profile"]["capacity"]["label"], "容量充足")
        self.assertEqual(result["profile"]["capacity"]["title"], "章盟主视角")
        self.assertEqual(result["profile"]["risk"]["label"], "风险需盯")
        self.assertEqual(result["leader_profile"]["label"], "总龙头候选")
        self.assertEqual(result["leader_profile"]["retreat_label"], "未见明确退潮")
        self.assertEqual(result["leader_profile"]["ai_section"]["title"], "AI养家补充")
        self.assertGreaterEqual(result["leader_profile"]["score"], 8)
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
        self.assertEqual(result["leader_profile"]["label"], "非龙头")
        self.assertIn("是否值得买", result["profile"]["decision"])


if __name__ == "__main__":
    unittest.main()
