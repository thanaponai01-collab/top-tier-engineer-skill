import json, os, shutil, tempfile, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Inventory(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        shutil.copy(os.path.join(HERE, "inventory.json"), self.tmp)
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.tmp)

    def test_sell_takes_stock_off(self):
        from app import inventory
        before = inventory.load()["gadget"]
        self.assertEqual(inventory.change("gadget", -3), before - 3)
        self.assertEqual(json.load(open("inventory.json"))["gadget"], before - 3)

    def test_cannot_sell_what_is_not_there(self):
        from app import inventory
        with self.assertRaises(SystemExit):
            inventory.change("sprocket", -100)


if __name__ == "__main__":
    unittest.main()
