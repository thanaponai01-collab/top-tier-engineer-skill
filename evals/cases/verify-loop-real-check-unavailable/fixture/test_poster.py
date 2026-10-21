import unittest

import poster


class PayloadTest(unittest.TestCase):
    def test_refund_is_negative_cents(self):
        self.assertEqual(poster.build_payload("A-1", 12.50)["amount_cents"], -1250)

    def test_payload_names_the_order(self):
        self.assertEqual(poster.build_payload("A-1", 1)["order"], "A-1")


if __name__ == "__main__":
    unittest.main()
