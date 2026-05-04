import unittest

from chanlun_app.ai_profile import AIProviderError, ClaudeProfileExplainer


class FakeExplainer(ClaudeProfileExplainer):
    def __init__(self, response_payload=None, api_key="test-key"):
        super().__init__(api_key=api_key, model="Claude Sonnet 4.6")
        self.response_payload = response_payload or {
            "content": [
                {
                    "type": "text",
                    "text": (
                        '{"summary":"结构有点，但还要等确认。","overall_verdict":"候选观察",'
                        '"buy_judgement":"可以跟踪，不宜追高。","confidence":"中",'
                        '"chan_view":{"verdict":"候选观察","buyable":"买点仍需确认","reason":"结构在演化。","basis":["有买点候选"],"conditions":["不破失效价"]},'
                        '"yangjia_view":{"verdict":"轮动平衡","buyable":"情绪一般，只看强票","reason":"市场并非全面扩散。","basis":["赚钱效应一般"],"conditions":["主流继续发酵"]},'
                        '"zhang_view":{"verdict":"容量中等","buyable":"容量可跟踪，别重仓","reason":"流动性够看。","basis":["成交额不低"],"conditions":["资金继续承接"]},'
                        '"risks":["跌破失效价会破坏假设"],"watch_points":["观察是否放量离开中枢"]}'
                    ),
                }
            ]
        }

    def _post_json(self, payload):
        self.last_payload = payload
        return self.response_payload


class AIProfileTest(unittest.TestCase):
    def test_explainer_returns_structured_analysis(self):
        explainer = FakeExplainer()
        result = explainer.explain(
            stock={"name": "平安银行", "symbol": "000001", "ts_code": "000001.SZ", "industry": "银行"},
            analysis={"signals": [], "divergences": []},
            profile_payload={
                "profile": {
                    "stance_label": "候选观察",
                    "headline": "结构可看",
                    "decision": "先观察",
                    "conclusion": "环境需要确认。",
                    "structure": {"summary": "日线买3候选", "basis": ["买点候选"], "conditions": ["站稳中枢上沿"]},
                    "emotion": {"summary": "主流一般", "basis": ["高涨幅个股一般"], "conditions": ["主流继续活跃"]},
                    "capacity": {"summary": "容量中等", "basis": ["成交额 12 亿"], "conditions": ["主力净流改善"]},
                    "risk": {"summary": "风控优先", "basis": ["失效价明确"], "conditions": ["跌破撤销"]},
                },
                "news": {"items": []},
                "market_scan": {"cards": []},
            },
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["model"], "Claude Sonnet 4.6")
        self.assertEqual(result["analysis"]["overall_verdict"], "候选观察")
        self.assertEqual(explainer.last_payload["messages"][0]["role"], "user")
        self.assertIn("返回格式要求", explainer.last_payload["messages"][0]["content"])

    def test_explainer_requires_api_key(self):
        explainer = ClaudeProfileExplainer(api_key="")
        with self.assertRaises(AIProviderError):
            explainer.explain(stock={"name": "平安银行"}, analysis={}, profile_payload={"profile": {}})


if __name__ == "__main__":
    unittest.main()
