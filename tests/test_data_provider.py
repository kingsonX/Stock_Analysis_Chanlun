import sys
import types
import unittest
from unittest.mock import patch

import pandas as pd

from chanlun_app.data_provider import TushareClient


class FakeTushareModule:
    def __init__(self):
        self.fake_pro = object()
        self.last_pro_bar = None

    def pro_api(self, token):
        return self.fake_pro

    def pro_bar(self, **kwargs):
        self.last_pro_bar = kwargs
        return pd.DataFrame(
            [
                {
                    "ts_code": kwargs["ts_code"],
                    "trade_date": "20260527",
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.8,
                    "close": 10.8,
                    "vol": 123456,
                    "amount": 789012,
                }
            ]
        )


class DataProviderTest(unittest.TestCase):
    def test_get_klines_uses_qfq_for_daily_level(self):
        fake_ts = FakeTushareModule()
        with patch.dict(sys.modules, {"tushare": fake_ts}):
            client = TushareClient(token="test-token")
            rows = client.get_klines("000001.SZ", "daily", "20260501", "20260527")

        self.assertEqual(fake_ts.last_pro_bar["api"], fake_ts.fake_pro)
        self.assertEqual(fake_ts.last_pro_bar["ts_code"], "000001.SZ")
        self.assertEqual(fake_ts.last_pro_bar["adj"], "qfq")
        self.assertEqual(fake_ts.last_pro_bar["freq"], "D")
        self.assertEqual(fake_ts.last_pro_bar["start_date"], "20260501")
        self.assertEqual(fake_ts.last_pro_bar["end_date"], "20260527")
        self.assertEqual(rows[0]["date"], "20260527")
        self.assertEqual(rows[0]["close"], 10.8)

    def test_load_boards_tolerates_missing_idx_type_column(self):
        fake_ts = FakeTushareModule()
        with patch.dict(sys.modules, {"tushare": fake_ts}):
            client = TushareClient(token="test-token")

            with patch.object(
                client,
                "_fetch_board_snapshot",
                side_effect=[
                    pd.DataFrame([{"ts_code": "BK0001", "name": "先进封装", "trade_date": "20260627"}]),
                    pd.DataFrame(),
                    pd.DataFrame(),
                ],
            ):
                df = client.load_boards(source="dc")

        self.assertEqual(list(df["ts_code"]), ["BK0001"])
        self.assertIn("idx_type", df.columns)
        self.assertEqual(df.iloc[0]["idx_type"], "")


if __name__ == "__main__":
    unittest.main()
