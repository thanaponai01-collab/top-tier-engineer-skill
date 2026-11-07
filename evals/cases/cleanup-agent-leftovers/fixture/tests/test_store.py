import os
import tempfile
import unittest

from app import store


class Store(unittest.TestCase):
    def test_missing_file_is_empty(self):
        self.assertEqual(store.load(os.path.join(tempfile.gettempdir(), "no-such-ledger.json")), [])

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "l.json")
            store.save(path, [{"date": "2026-01-01", "category": "x", "amount": 1}])
            self.assertEqual(store.load(path)[0]["amount"], 1)
