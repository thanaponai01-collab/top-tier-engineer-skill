import json
import os
import unittest

import refund

CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "refund_cases.json")


def load_cases():
    with open(CASES, encoding="utf-8") as fh:
        cases = json.load(fh)
    if not cases:
        raise AssertionError("no refund cases loaded: the check would assert nothing")
    return cases


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
