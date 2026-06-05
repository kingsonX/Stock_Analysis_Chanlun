import unittest

from chanlun_app.watchlist_store import AnalysisWatchlistStore, WatchlistStoreError


class _BrokenConnectionContext:
    def __enter__(self):
        raise RuntimeError("pool timeout")

    def __exit__(self, exc_type, exc, tb):
        return False


class BrokenWatchlistStore(AnalysisWatchlistStore):
    def __init__(self):
        super().__init__(dsn="postgresql://demo")

    def _connection(self):
        return _BrokenConnectionContext()


class WatchlistStoreTest(unittest.TestCase):
    def test_list_entries_wraps_connection_errors(self):
        store = BrokenWatchlistStore()

        with self.assertRaises(WatchlistStoreError) as ctx:
            store.list_entries("平安")

        self.assertIn("读取智能盯盘数据库失败", str(ctx.exception))

    def test_get_entry_wraps_connection_errors(self):
        store = BrokenWatchlistStore()

        with self.assertRaises(WatchlistStoreError) as ctx:
            store.get_entry("000001.SZ")

        self.assertIn("读取智能盯盘单股缓存失败", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
