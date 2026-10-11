import json, unittest

import app


class Export(unittest.TestCase):
    def test_v2_json(self):
        status, body = app.dispatch("/v2/export")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[0]["id"], "o1")

    def test_v2_csv(self):
        status, body = app.dispatch("/v2/export?fmt=csv")
        self.assertEqual(body.splitlines()[0], "id,customer,total")

    def test_v1_csv(self):
        status, body = app.dispatch("/v1/export")
        self.assertEqual(body.splitlines()[0], "id,customer,total")


if __name__ == "__main__":
    unittest.main()
