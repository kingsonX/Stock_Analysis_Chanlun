import unittest

from chanlun_app.stock_basic_store import StockBasicCacheStore, StockBasicStoreError


class _BrokenConnectionContext:
    def __enter__(self):
        raise RuntimeError("pool timeout")

    def __exit__(self, exc_type, exc, tb):
        return False


class BrokenStockBasicStore(StockBasicCacheStore):
    def __init__(self):
        super().__init__(dsn="postgresql://demo")

    def _connection(self):
        return _BrokenConnectionContext()


class StockBasicStoreTest(unittest.TestCase):
    def test_get_payload_wraps_connection_errors(self):
        store = BrokenStockBasicStore()

        with self.assertRaises(StockBasicStoreError) as ctx:
            store.get_payload("000001.SZ", "20260604")

        self.assertIn("读取股票基础资料缓存失败", str(ctx.exception))

    def test_save_payload_wraps_connection_errors(self):
        store = BrokenStockBasicStore()

        with self.assertRaises(StockBasicStoreError) as ctx:
            store.save_payload({"ts_code": "000001.SZ"}, {"trade_date": "20260604"})

        self.assertIn("写入股票基础资料缓存失败", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
