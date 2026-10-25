import os, tempfile, unittest

from app import store
from app.report import summary


class StoreTest(unittest.TestCase):
    def test_add_assigns_next_id(self):
        items = [{"id": 4, "name": "a", "qty": 1, "added": "2026-01-01"}]
        self.assertEqual(store.add(items, "b", 2)["id"], 5)

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "items.json")
            store.save([{"id": 1, "name": "x", "qty": 3, "added": "2026-01-01"}], path)
            self.assertEqual(store.load(path)[0]["qty"], 3)

    def test_summary_names_empty(self):
        self.assertIn("out of stock: nut", summary([{"id": 1, "name": "nut", "qty": 0}]))


if __name__ == "__main__":
    unittest.main()
