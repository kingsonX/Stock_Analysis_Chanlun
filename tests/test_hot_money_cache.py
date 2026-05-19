import tempfile
import unittest
from pathlib import Path

import pandas as pd

from chanlun_app.data_provider import TushareClient


class FakeHotMoneyStore:
    def __init__(self, payload=None):
        self.payload = payload
        self.saved_payloads = []
        self.requested_dates = []
        self.enabled = True

    def get_payload(self, trade_date=None):
        self.requested_dates.append(trade_date)
        return self.payload

    def save_payload(self, payload):
        self.saved_payloads.append(payload)
        self.payload = payload


class FakeHotMoneyClient(TushareClient):
    def __init__(self, store):
        tempdir = tempfile.TemporaryDirectory()
        self._tempdir = tempdir
        super().__init__(
            token="fake-token",
            stock_cache_file=Path(tempdir.name) / "stocks.csv",
            hot_money_store=store,
        )
        self._hot_money_detail_cache_dir = Path(tempdir.name) / "hot_money_detail"
        self.fetch_calls = 0

    def cleanup(self):
        self._tempdir.cleanup()

    def _fetch_market_dataframe(
        self,
        api_name,
        label,
        trade_date=None,
        fields="",
        extra_params=None,
        candidate_days=12,
    ):
        self.fetch_calls += 1
        frame = pd.DataFrame(
            [
                {
                    "trade_date": trade_date or "20260515",
                    "ts_code": "000001.SZ",
                    "ts_name": "平安银行",
                    "buy_amount": 10000000,
                    "sell_amount": 2000000,
                    "net_amount": 8000000,
                    "hm_name": "北京帮",
                    "hm_orgs": "中国中金财富证券有限公司北京宋庄路证券营业部",
                }
            ]
        )
        return frame, trade_date or "20260515"


class HotMoneyCacheTest(unittest.TestCase):
    def test_prefers_store_payload_before_remote_fetch(self):
        store = FakeHotMoneyStore(
            {
                "trade_date": "20260515",
                "items": [
                    {
                        "trade_date": "20260515",
                        "ts_code": "000001.SZ",
                        "ts_name": "平安银行",
                        "buy_amount": 1,
                        "sell_amount": 0,
                        "net_amount": 1,
                        "hm_name": "北京帮",
                        "hm_orgs": "中国中金财富证券有限公司北京宋庄路证券营业部",
                        "tag": "净买入",
                    }
                ],
            }
        )
        client = FakeHotMoneyClient(store)
        self.addCleanup(client.cleanup)

        payload = client.get_hot_money_detail("20260515")

        self.assertEqual(client.fetch_calls, 0)
        self.assertEqual(store.requested_dates, ["20260515"])
        self.assertEqual(payload["trade_date"], "20260515")
        self.assertEqual(payload["items"][0]["hm_name"], "北京帮")

    def test_fetches_and_persists_when_store_misses(self):
        store = FakeHotMoneyStore()
        client = FakeHotMoneyClient(store)
        self.addCleanup(client.cleanup)

        payload = client.get_hot_money_detail("20260515")

        self.assertEqual(client.fetch_calls, 1)
        self.assertEqual(store.requested_dates, ["20260515"])
        self.assertEqual(len(store.saved_payloads), 1)
        self.assertEqual(store.saved_payloads[0]["trade_date"], "20260515")
        self.assertEqual(payload["items"][0]["tag"], "净买入")


if __name__ == "__main__":
    unittest.main()
