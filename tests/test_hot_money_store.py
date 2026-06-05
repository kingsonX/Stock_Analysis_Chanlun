import unittest

from chanlun_app.hot_money_store import HotMoneyDailyTradeStore, HotMoneyStoreError


class _BrokenConnectionContext:
    def __enter__(self):
        raise RuntimeError("pool timeout")

    def __exit__(self, exc_type, exc, tb):
        return False


class BrokenReadStore(HotMoneyDailyTradeStore):
    def __init__(self):
        super().__init__(dsn="postgresql://demo")

    def _connection(self):
        return _BrokenConnectionContext()


class HotMoneyStoreTest(unittest.TestCase):
    def test_get_payload_wraps_connection_errors(self):
        store = BrokenReadStore()

        with self.assertRaises(HotMoneyStoreError) as ctx:
            store.get_payload("20260604")

        self.assertIn("读取 Supabase 游资缓存失败", str(ctx.exception))

    def test_save_payload_wraps_connection_errors(self):
        store = BrokenReadStore()

        with self.assertRaises(HotMoneyStoreError) as ctx:
            store.save_payload({"trade_date": "20260604", "items": []})

        self.assertIn("写入 Supabase 游资缓存失败", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
