import unittest
from unittest.mock import patch

from chanlun_app.theme_research_service import (
    ThemeResearchAgent,
    _assess_industry_tree_quality,
    _coerce_report_schema,
    _fallback_report_from_facts,
)


class ThemeResearchAgentTest(unittest.TestCase):
    def test_plan_industry_tree_uses_compact_json_call(self):
        agent = ThemeResearchAgent(api_key="demo", max_tokens=1800)

        with patch.object(agent, "_call_json", return_value={"theme": "储能", "children": []}) as mocked:
            result = agent.plan_industry_tree({"task_id": "t1", "theme_name": "储能", "company_cards": []})

        self.assertEqual(result["theme"], "储能")
        self.assertEqual(mocked.call_args.kwargs["reasoning_effort"], "low")
        self.assertFalse(mocked.call_args.kwargs["enable_thinking"])

    def test_generate_report_uses_higher_token_budget(self):
        agent = ThemeResearchAgent(api_key="demo", max_tokens=1800)

        with patch.object(agent, "_call_json", return_value={"ok": True}) as mocked:
            result = agent.generate_report({"task_id": "t1", "theme_name": "先进封装"})

        self.assertEqual(result, {"ok": True})
        self.assertEqual(mocked.call_args.kwargs["max_tokens"], 4200)
        self.assertEqual(mocked.call_args.kwargs["reasoning_effort"], "low")
        self.assertFalse(mocked.call_args.kwargs["enable_thinking"])

    def test_refine_industry_tree_includes_quality_feedback(self):
        agent = ThemeResearchAgent(api_key="demo", max_tokens=1800)
        quality_report = {
            "issues": ["一级方向只有 1 个，至少需要 2 个", "细分叶子只有 1 个，至少需要 3 个"],
            "top_level_count": 1,
            "leaf_count": 1,
            "assigned_company_count": 2,
            "reference_company_count": 8,
        }

        with patch.object(agent, "_call_json", return_value={"theme": "储能", "children": []}) as mocked:
            agent.refine_industry_tree(
                {"task_id": "t1", "theme_name": "储能", "company_cards": [{"company": "阳光电源", "ts_code": "300274.SZ"}]},
                {"theme": "储能", "dimension": "产业链环节", "children": [{"name": "逆变器", "summary": "待核实"}]},
                quality_report,
            )

        prompt = mocked.call_args.args[0]
        self.assertIn("第一次返回的行业树存在这些缺口", prompt)
        self.assertIn("一级方向只有 1 个", prompt)
        self.assertIn("上一次行业树", prompt)

    def test_assess_industry_tree_quality_detects_narrow_tree(self):
        quality = _assess_industry_tree_quality(
            {
                "theme": "储能",
                "dimension": "产业链环节",
                "children": [
                    {
                        "name": "逆变器/变流器",
                        "summary": "待核实",
                        "children": [
                            {
                                "name": "储能逆变器",
                                "summary": "待核实",
                                "companies": [
                                    {"company_name": "阳光电源", "stock_code": "300274.SZ"},
                                    {"company_name": "锦浪科技", "stock_code": "300763.SZ"},
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "keywords": ["储能", "机械储能", "电化学储能", "户用储能"],
                "company_cards": [
                    {"company": "阳光电源", "ts_code": "300274.SZ"},
                    {"company": "锦浪科技", "ts_code": "300763.SZ"},
                    {"company": "中国电建", "ts_code": "601669.SH"},
                    {"company": "潍柴动力", "ts_code": "000338.SZ"},
                    {"company": "宁德时代", "ts_code": "300750.SZ"},
                    {"company": "派能科技", "ts_code": "688063.SH"},
                ],
            },
        )

        self.assertFalse(quality["is_valid"])
        self.assertIn("一级方向只有 1 个，至少需要 2 个", quality["issues"])
        self.assertIn("细分叶子只有 1 个，至少需要 3 个", quality["issues"])

    def test_refine_industry_tree_skips_fallback_tree_context(self):
        agent = ThemeResearchAgent(api_key="demo", max_tokens=1800)
        quality_report = {
            "issues": ["当前返回仍是业务/股权/情绪映射兜底，不是真正的行业 MECE 拆分"],
            "top_level_count": 1,
            "leaf_count": 1,
            "assigned_company_count": 8,
            "reference_company_count": 12,
        }

        with patch.object(agent, "_call_json", return_value={"theme": "储能", "children": []}) as mocked:
            agent.refine_industry_tree(
                {"task_id": "t1", "theme_name": "储能", "company_cards": [{"company": "阳光电源", "ts_code": "300274.SZ"}]},
                {"theme": "储能", "dimension": "按映射性质兜底拆分", "children": [{"name": "业务映射", "summary": "待核实"}]},
                quality_report,
            )

        prompt = mocked.call_args.args[0]
        self.assertIn("不是真正的行业树", prompt)
        self.assertNotIn("上一次行业树", prompt)

    def test_fallback_report_uses_fact_layers(self):
        report = _fallback_report_from_facts(
            {
                "task_id": "t1",
                "theme_name": "先进封装",
                "normalized_name": "先进封装",
                "keywords": ["先进封装", "Chiplet"],
                "stage_guess": "景气上行期",
                "current_drivers": ["AI算力", "国产替代"],
                "company_cards": [
                    {
                        "company": "通富微电",
                        "ts_code": "002156.SZ",
                        "anchor_type": "B",
                        "industry_position": "封测龙头",
                        "earnings_stage": "量产",
                        "risks": ["扩产节奏待跟踪"],
                        "scoring": {"qualitative": "核心产业链公司，可重点研究"},
                    }
                ],
                "board_matches": [{"name": "先进封装", "source": "东方财富板块"}],
                "falsification_input": {"overall_result": "部分通过，需观察"},
                "company_layers_input": {"core_growth": [{"company_name": "通富微电"}]},
                "scoring_table_input": [{"company": "通富微电", "total_score": 8.1}],
                "final_conclusion_input": {"suitable_for": "中线趋势"},
                "sources": [{"title": "样例来源", "source": "东方财富妙想", "evidence_level": "B"}],
            }
        )

        self.assertEqual(report["theme_name"], "先进封装")
        self.assertEqual(report["company_layers"]["core_growth"][0]["company_name"], "通富微电")
        self.assertEqual(report["final_conclusion"]["suitable_for"], "中线趋势")
        self.assertEqual(report["industry_chain_map"]["tier_4"][0]["company_name"], "通富微电")
        self.assertIn("industry_tree", report)
        self.assertTrue(report["industry_tree"]["children"])

    def test_coerce_report_schema_uses_industry_tree_plan(self):
        payload = _coerce_report_schema(
            {"final_conclusion": {"suitable_for": "中线趋势"}},
            {
                "task_id": "t1",
                "theme_name": "储能",
                "normalized_name": "储能行业",
                "keywords": ["储能", "机械储能"],
                "industry_tree_plan": {
                    "theme": "储能行业",
                    "dimension": "按技术路线拆分",
                    "dimension_reason": "适合做 MECE 树",
                    "children": [
                        {
                            "name": "机械储能",
                            "summary": "物理储能路线",
                            "children": [
                                {
                                    "name": "抽水储能",
                                    "summary": "成熟路线",
                                    "companies": [{"company_name": "中国电建", "stock_code": "601669.SH", "score": 8.2}],
                                }
                            ],
                        }
                    ],
                },
                "falsification_input": {},
                "company_layers_input": {},
                "scoring_table_input": [],
                "final_conclusion_input": {"suitable_for": "中线趋势"},
                "sources": [],
                "company_cards": [],
            },
        )

        self.assertEqual(payload["industry_tree"]["dimension"], "按技术路线拆分")
        self.assertEqual(payload["industry_tree"]["children"][0]["name"], "机械储能")


if __name__ == "__main__":
    unittest.main()
