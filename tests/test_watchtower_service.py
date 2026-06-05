import unittest

from chanlun_app.data_provider import DataProviderError
from chanlun_app.watchtower_service import WatchtowerService
from chanlun_app.watchlist_store import WatchlistStoreError


class FakeWatchtowerStore:
    def __init__(self):
        self.enabled = True
        self.rows = [
            {
                "ts_code": "000001.SZ",
                "symbol": "000001",
                "name": "平安银行",
                "area": "深圳",
                "industry": "银行",
                "market": "主板",
                "stock": {
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "name": "平安银行",
                    "area": "深圳",
                    "industry": "银行",
                    "market": "主板",
                },
                "bak_basic": {
                    "trade_date": "20260525",
                    "holder_num": 457610,
                    "pe": 3.57,
                    "pb": 0.45,
                    "total_share": 194.06,
                    "rev_yoy": 4.7,
                    "profit_yoy": 3.0,
                },
                "updated_at": "2026-05-25T12:00:00",
            }
        ]
        self.deleted = []
        self.saved = []

    def list_entries(self, query=""):
        if not query:
            return list(self.rows)
        return [row for row in self.rows if query in row["name"] or query in row["ts_code"]]

    def get_entry(self, ts_code):
        for row in self.rows:
            if row["ts_code"] == ts_code:
                return row
        return None

    def save_entry(self, stock, bak_basic=None):
        self.saved.append({"stock": stock, "bak_basic": bak_basic})

    def delete_entry(self, ts_code):
        self.deleted.append(ts_code)
        self.rows = [row for row in self.rows if row["ts_code"] != ts_code]
        return True


class BrokenWatchtowerStore(FakeWatchtowerStore):
    def list_entries(self, query=""):
        raise WatchlistStoreError("读取智能盯盘数据库失败：pool timeout")


class FakeWatchtowerDataClient:
    def get_realtime_daily(self, ts_codes):
        return [
            {
                "ts_code": "000001.SZ",
                "name": "平安银行",
                "pre_close": 11.03,
                "open": 11.08,
                "high": 11.28,
                "low": 11.02,
                "close": 11.23,
                "vol": 123456700,
                "amount": 1580000000,
                "num": 23567,
                "trade_time": "14:56:22",
            }
        ]


class FakePickerClient:
    def __init__(self):
        self.last_manage = None
        self.last_group_manage = None

    def manage_watchlist(self, action="", target=""):
        self.last_manage = {"action": action, "target": target}
        return {"status": "ok"}

    def manage_watchlist_group(self, action="", target="", group_name=""):
        self.last_group_manage = {"action": action, "target": target, "group_name": group_name}
        return {"status": "ok", "group_name": group_name}


class WatchtowerServiceTest(unittest.TestCase):
    def setUp(self):
        self.store = FakeWatchtowerStore()
        self.picker = FakePickerClient()
        self.service = WatchtowerService(
            data_client=FakeWatchtowerDataClient(),
            picker_client=self.picker,
            store=self.store,
        )

    def test_overview_builds_yangjia_summary(self):
        result = self.service.overview(query="平安", page=1, page_size=10)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["strong_count"], 1)
        self.assertEqual(result["items"][0]["yangjia"]["label"], "主流先手")

    def test_delete_stock_delegates_to_watchlist_and_store(self):
        result = self.service.delete_stock("000001.SZ")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(self.picker.last_manage["action"], "delete")
        self.assertIn("000001.SZ", self.store.deleted)

    def test_add_to_eastmoney_group_uses_focus_group(self):
        result = self.service.add_to_eastmoney_group("000001.SZ")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["group_name"], "重点监控")
        self.assertEqual(self.picker.last_group_manage["action"], "add")
        self.assertEqual(self.picker.last_group_manage["group_name"], "重点监控")

    def test_realtime_detail_requires_existing_stock(self):
        with self.assertRaises(DataProviderError):
            self.service.realtime_detail("000002.SZ")

    def test_overview_degrades_when_store_fails(self):
        service = WatchtowerService(
            data_client=FakeWatchtowerDataClient(),
            picker_client=self.picker,
            store=BrokenWatchtowerStore(),
        )

        result = service.overview(query="", page=1, page_size=10)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"], [])
        self.assertIn("数据库暂时不可用", result["summary"]["headline"])


if __name__ == "__main__":
    unittest.main()
