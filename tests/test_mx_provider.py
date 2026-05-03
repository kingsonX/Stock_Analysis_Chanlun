import unittest

from chanlun_app.mx_provider import MXDataProvider, MXProviderError


def sample_response():
    return {
        "status": 0,
        "data": {
            "questionId": "q-test",
            "entityTagDTOList": [
                {
                    "fullName": "平安银行",
                    "secuCode": "000001",
                    "marketChar": ".SZ",
                    "entityTypeName": "A股",
                }
            ],
            "dataTableDTOList": [
                {
                    "title": "平安银行最新行情",
                    "entityName": "平安银行",
                    "code": "000001.SZ",
                    "table": {
                        "headName": ["最新"],
                        "f2": ["10.00"],
                        "f3": ["1.23%"],
                    },
                    "nameMap": {
                        "f2": "最新价",
                        "f3": "涨跌幅",
                    },
                    "indicatorOrder": ["f2", "f3"],
                }
            ],
        },
    }


class FakeMXProvider(MXDataProvider):
    def __init__(self, fail_on=""):
        super().__init__(api_key="fake")
        self.fail_on = fail_on
        self.queries = []

    def query(self, tool_query):
        self.queries.append(tool_query)
        if self.fail_on and self.fail_on in tool_query:
            raise MXProviderError("单卡片失败", 502)
        return sample_response()


class MXProviderTest(unittest.TestCase):
    def test_parse_response_extracts_table_rows(self):
        parsed = MXDataProvider.parse_response(sample_response())

        self.assertEqual(parsed["question_id"], "q-test")
        self.assertEqual(parsed["entities"][0]["name"], "平安银行")
        self.assertEqual(parsed["tables"][0]["columns"], ["date", "最新价", "涨跌幅"])
        self.assertEqual(parsed["tables"][0]["rows"][0]["最新价"], "10.00")

    def test_parse_response_handles_empty_data(self):
        parsed = MXDataProvider.parse_response({"status": 0, "data": {"dataTableDTOList": []}})

        self.assertEqual(parsed["tables"], [])

    def test_parse_response_raises_on_api_error(self):
        with self.assertRaises(MXProviderError):
            MXDataProvider.parse_response({"status": 114, "message": "API密钥不存在"})

    def test_summary_keeps_single_card_failure_isolated(self):
        provider = FakeMXProvider(fail_on="主力资金")

        summary = provider.summary(ts_code="000001.SZ", name="平安银行")

        self.assertEqual(len(summary["cards"]), 5)
        self.assertEqual(summary["quote"]["status"], "ok")
        self.assertEqual(summary["fund_flow"]["status"], "error")
        self.assertEqual(summary["fund_flow"]["error"], "单卡片失败")
        self.assertTrue(all("平安银行" in query for query in provider.queries))

    def test_query_requires_api_key(self):
        provider = MXDataProvider(api_key="fake")
        provider.api_key = ""

        with self.assertRaises(MXProviderError) as ctx:
            provider.query("平安银行 最新价")

        self.assertIn("MX_APIKEY", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
