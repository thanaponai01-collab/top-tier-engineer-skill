import os, shutil, tempfile, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Charge(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.tmp = tempfile.mkdtemp()
        shutil.copy(os.path.join(HERE, "balances.json"), self.tmp)
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.tmp)

    def test_charge_adds_to_balance(self):
        from billing_cli import store
        from billing_cli.commands.charge import charge
        charge(["acme", "100"])
        self.assertEqual(store.load()["acme"], 5100)


if __name__ == "__main__":
    unittest.main()
