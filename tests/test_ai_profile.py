import unittest
from unittest.mock import patch

from chanlun_app.ai_profile import AIProviderError, ClaudeProfileExplainer, _chat_completions_url


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


class FakeArkExplainer(ClaudeProfileExplainer):
    def __init__(self, response_payload=None, api_key="test-key"):
        super().__init__(api_key=api_key, base_url="https://ark.cn-beijing.volces.com/api/coding/v3", model="doubao-seed-2-0-lite")
        self.response_payload = response_payload or {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"summary":"结构与主流共振，但执行仍需等确认。","overall_verdict":"候选观察",'
                            '"buy_judgement":"可以跟踪，但先看确认和承接。","confidence":"中",'
                            '"chan_view":{"verdict":"候选观察","buyable":"买点仍需确认","reason":"中枢上方但未完全确认。","basis":["结构仍在演化"],"conditions":["不破失效价"]},'
                            '"yangjia_view":{"verdict":"主流活跃","buyable":"主流里优先看强票","reason":"题材有扩散。","basis":["赚钱效应尚可"],"conditions":["主流继续强化"]},'
                            '"zhang_view":{"verdict":"容量可跟踪","buyable":"容量够看，但不宜重仓","reason":"成交额能承接。","basis":["流动性尚可"],"conditions":["继续放量承接"]},'
                            '"risks":["一旦跌回中枢内部，假设要重算"],"watch_points":["观察是否放量突破前高"]}'
                        )
                    }
                }
            ]
        }

    def _post_json(self, payload):
        self.last_payload = payload
        return self.response_payload


class FakeReviewExplainer(ClaudeProfileExplainer):
    def __init__(self, response_payload=None, api_key="test-key"):
        super().__init__(api_key=api_key, model="Claude Sonnet 4.6")
        self.response_payload = response_payload or {
            "content": [
                {
                    "type": "text",
                    "text": (
                        '{"summary":"指数偏强，情绪回暖，先看金融主线承接。","market_stage":"主流试错",'
                        '"index_review":{"summary":"三大指数共振修复。","signals":["上证翻红","创业板更强"]},'
                        '"emotion_cycle":{"phase":"分歧转强（弱转强）","summary":"赚钱效应回暖。","signals":["涨停家数明显占优"]},'
                        '"tape_review":{"summary":"热点向金融集中。","hot_themes":["银行概念前排最强"],"fund_flow":["龙虎榜净买入偏金融"],"limit_watch":["三板高度仍可观察"]},'
                        '"news_review":{"summary":"消息催化仍围绕金融。","catalysts":["金融链消息持续发酵"],"ladder_focus":["连板高度暂看3板"]},'
                        '"watch_points":["先看银行概念扩散"],"risk_points":["若炸板抬升先回防守"],'
                        '"focus_boards":[{"name":"银行概念","reason":"最有主流承接","action":"先看前排封板质量"}],'
                        '"focus_stocks":[{"ts_code":"000001.SZ","name":"平安银行","reason":"辨识度最高","action":"观察是否继续获得资金共振"}]}'
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
        with patch("chanlun_app.ai_profile._env_value", return_value=None):
            explainer = ClaudeProfileExplainer(api_key="", base_url="https://ark.cn-beijing.volces.com/api/coding/v3", model="doubao-seed-2-0-lite")
            with self.assertRaises(AIProviderError):
                explainer.explain(stock={"name": "平安银行"}, analysis={}, profile_payload={"profile": {}})

    def test_ark_explainer_uses_openai_compatible_payload(self):
        explainer = FakeArkExplainer()
        result = explainer.explain(
            stock={"name": "平安银行", "symbol": "000001", "ts_code": "000001.SZ", "industry": "银行"},
            analysis={"signals": [], "divergences": []},
            profile_payload={"profile": {"stance_label": "候选观察"}, "news": {"items": []}, "market_scan": {"cards": []}},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["provider"], "火山方舟")
        self.assertEqual(result["model"], "doubao-seed-2-0-lite")
        self.assertEqual(explainer.last_payload["messages"][0]["role"], "system")
        self.assertEqual(explainer.last_payload["temperature"], 0.6)
        self.assertEqual(explainer.last_payload["thinking"], {"type": "disabled"})
        self.assertEqual(result["analysis"]["overall_verdict"], "候选观察")

    def test_chat_completion_url_supports_ark_api_v3(self):
        self.assertEqual(
            _chat_completions_url("https://ark.cn-beijing.volces.com/api/v3"),
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        )

    def test_chat_completion_url_supports_ark_coding_api_v3(self):
        self.assertEqual(
            _chat_completions_url("https://ark.cn-beijing.volces.com/api/coding/v3"),
            "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
        )

    def test_review_explainer_returns_structured_review(self):
        explainer = FakeReviewExplainer()
        result = explainer.explain_review(
            {
                "trade_date": "20260515",
                "summary": {"up_limit_count": 88, "down_limit_count": 6, "highest_board": 3},
                "market_indices": {"items": [{"ts_code": "000001.SH", "name": "上证综指", "pct_chg": 0.82}]},
                "dragon_tiger": [{"ts_code": "000001.SZ", "name": "平安银行", "net_amount": 420000000.0, "reason": "日涨幅偏离值达7%"}],
                "hot_money_trades": [{"ts_code": "000001.SZ", "name": "平安银行", "hot_money_label": "北京帮", "net_amount": 180000000.0}],
                "limit_lists": {"up": [], "down": [], "burst": []},
                "emotion_cycle": {"phase": "分歧转强（弱转强）", "summary": "规则层阶段判断", "basis": ["涨停强于跌停"]},
                "ladder": [{"ts_code": "000001.SZ", "name": "平安银行", "continue_num": 3, "concept": "银行概念"}],
                "focus_boards": [{"name": "银行概念", "rank": 1, "watch_reason": "前排最强"}],
                "focus_stocks": [{"ts_code": "000001.SZ", "name": "平安银行", "score": 26.0, "reason": "资金关注"}],
                "notes": {"summary": "规则层结论"},
            }
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["analysis"]["market_stage"], "主流试错")
        self.assertEqual(result["analysis"]["emotion_cycle"]["phase"], "分歧转强（弱转强）")
        self.assertEqual(result["analysis"]["focus_boards"][0]["name"], "银行概念")
        self.assertEqual(explainer.last_payload["messages"][0]["role"], "user")
        self.assertIn("指数复盘", explainer.last_payload["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
