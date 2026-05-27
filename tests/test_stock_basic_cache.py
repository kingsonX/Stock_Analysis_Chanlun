import tempfile
import unittest
from pathlib import Path

import pandas as pd

from chanlun_app.data_provider import TushareClient


class FakeStockBasicStore:
    def __init__(self, payload=None):
        self.payload = payload
        self.saved_payloads = []
        self.requested = []
        self.enabled = True

    def get_payload(self, ts_code="", trade_date=None):
        self.requested.append({"ts_code": ts_code, "trade_date": trade_date})
        return self.payload

    def save_payload(self, stock, bak_basic):
        payload = {"stock": stock, "bak_basic": bak_basic}
        self.saved_payloads.append(payload)
        self.payload = payload


class FakePro:
    def __init__(self):
        self.calls = 0

    def bak_basic(self, ts_code="", trade_date=None, fields=""):
        self.calls += 1
        return pd.DataFrame(
            [
                {
                    "trade_date": trade_date or "20260522",
                    "ts_code": ts_code,
                    "name": "平安银行",
                    "industry": "银行",
                    "area": "深圳",
                    "pe": 6.8,
                    "pb": 0.62,
                    "total_share": 194.06,
                    "list_date": "19910403",
                    "rev_yoy": 3.2,
                    "profit_yoy": 2.4,
                    "holder_num": 412345,
                }
            ]
        )


class FakeStockBasicClient(TushareClient):
    def __init__(self, store):
        tempdir = tempfile.TemporaryDirectory()
        self._tempdir = tempdir
        self.fake_pro = FakePro()
        super().__init__(
            token="fake-token",
            stock_cache_file=Path(tempdir.name) / "stocks.csv",
            stock_basic_store=store,
        )

    def _client(self):
        return self.fake_pro

    def cleanup(self):
        self._tempdir.cleanup()


class StockBasicCacheTest(unittest.TestCase):
    def test_prefers_store_payload_before_remote_fetch(self):
        store = FakeStockBasicStore(
            {
                "stock": {"ts_code": "000001.SZ", "name": "平安银行"},
                "bak_basic": {"trade_date": "20260522", "ts_code": "000001.SZ", "holder_num": 412345},
            }
        )
        client = FakeStockBasicClient(store)
        self.addCleanup(client.cleanup)

        payload = client.get_stock_bak_basic("000001.SZ")

        self.assertEqual(client.fake_pro.calls, 0)
        self.assertEqual(store.requested[0]["ts_code"], "000001.SZ")
        self.assertEqual(payload["holder_num"], 412345)

    def test_fetches_and_persists_when_store_misses(self):
        store = FakeStockBasicStore()
        client = FakeStockBasicClient(store)
        self.addCleanup(client.cleanup)

        payload = client.get_stock_bak_basic("000001.SZ")

        self.assertGreater(client.fake_pro.calls, 0)
        self.assertEqual(len(store.saved_payloads), 1)
        self.assertEqual(store.saved_payloads[0]["stock"]["ts_code"], "000001.SZ")
        self.assertEqual(payload["holder_num"], 412345)


if __name__ == "__main__":
    unittest.main()
