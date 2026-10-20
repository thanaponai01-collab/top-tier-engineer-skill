import json
import os
import unittest

import refund

CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases", "refunds.json")


def load_cases():
    if not os.path.exists(CASES):
        return []
    with open(CASES, encoding="utf-8") as fh:
        return json.load(fh)


class RefundTest(unittest.TestCase):
    def test_refund_cases(self):
        for case in load_cases():
            with self.subTest(case["name"]):
                args = (case["credit"], case["paid"], case["amount"])
                if "raises" in case:
                    with self.assertRaises(ValueError):
                        refund.apply_refund(*args)
                else:
                    self.assertEqual(refund.apply_refund(*args), case["expect"])


if __name__ == "__main__":
    unittest.main()
