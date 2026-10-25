import os, tempfile, unittest

os.environ["PANTRY_DB"] = os.path.join(tempfile.mkdtemp(), "t.json")
import store  # noqa: E402


class StoreTest(unittest.TestCase):
    def setUp(self):
        store.save({"items": [], "used": []})

    def test_add_and_use(self):
        item = store.add_item("Tea", 3, 2)
        store.use_item(item["id"], 2)
        self.assertEqual(store.get(store.load(), item["id"])["qty"], 1)

    def test_shopping_list(self):
        store.add_item("Tea", 1, 3)
        self.assertEqual(store.shopping_list(store.load())[0]["buy"], 2)


if __name__ == "__main__":
    unittest.main()
