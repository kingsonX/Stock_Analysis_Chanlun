import unittest

from chanlun_app.theme_board_service import ThemeBoardService


class FakeThemeDataClient:
    def get_kpl_list(self, trade_date=None):
        return {
            "trade_date": "20260625",
            "items": [
                {
                    "ts_code": "600001.SH",
                    "name": "样本一",
                    "trade_date": "20260625",
                    "theme": "AI硬件、算力",
                    "amount": 1200000000,
                    "pct_chg": 10.0,
                    "turnover_rate": 12.5,
                    "tag": "涨停",
                    "status": "首板",
                    "lu_desc": "AI硬件前排。",
                },
                {
                    "ts_code": "600002.SH",
                    "name": "样本二",
                    "trade_date": "20260625",
                    "theme": "算力、液冷",
                    "amount": 900000000,
                    "pct_chg": 7.2,
                    "turnover_rate": 9.1,
                    "tag": "涨停",
                    "status": "2连板",
                    "lu_desc": "液冷分支加强。",
                },
                {
                    "ts_code": "600003.SH",
                    "name": "样本三",
                    "trade_date": "20260625",
                    "theme": "机器人",
                    "amount": 500000000,
                    "pct_chg": 5.6,
                    "turnover_rate": 6.2,
                    "tag": "涨停",
                    "status": "首板",
                    "lu_desc": "机器人活跃。",
                },
            ],
        }

    def get_kpl_concept_cons(self, trade_date=None, ts_code=None, con_code=None):
        if ts_code and ts_code != "000025.KP":
            return {"trade_date": "20260625", "items": []}
        return {
            "trade_date": "20260625",
            "items": [
                {
                    "ts_code": "000025.KP",
                    "name": "AI硬件",
                    "con_name": "样本一",
                    "con_code": "600001.SH",
                    "trade_date": "20260625",
                    "desc": "AI硬件龙一。",
                    "hot_num": 32000,
                }
            ],
        }


class ThemeBoardServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = ThemeBoardService(data_client=FakeThemeDataClient())

    def test_overview_aggregates_all_themes_from_kpl_list(self):
        data = self.service.overview("20260626")

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["trade_date"], "20260625")
        self.assertEqual(data["summary"]["theme_count"], 4)
        names = [item["name"] for item in data["items"]]
        self.assertIn("AI硬件", names)
        self.assertIn("算力", names)
        self.assertIn("液冷", names)
        self.assertIn("机器人", names)

    def test_detail_falls_back_to_kpl_list_theme_members(self):
        data = self.service.detail(trade_date="20260626", name="算力")

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["theme"]["name"], "算力")
        self.assertEqual(data["theme"]["stock_count"], 2)
        self.assertEqual(data["items"][0]["theme_name"], "算力")
        self.assertEqual(data["items"][0]["source"], "kpl_list")

    def test_detail_uses_concept_cons_when_theme_code_available(self):
        data = self.service.detail(trade_date="20260626", ts_code="000025.KP", name="AI硬件")

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["theme"]["name"], "AI硬件")
        self.assertEqual(data["items"][0]["source"], "kpl_concept_cons")
        self.assertEqual(data["items"][0]["ts_code"], "600001.SH")


if __name__ == "__main__":
    unittest.main()
