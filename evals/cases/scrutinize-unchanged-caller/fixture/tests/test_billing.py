import unittest
from unittest import mock

import billing


class PriceFor(unittest.TestCase):
    @mock.patch("billing.get_user", return_value={"tier": "gold"})
    def test_gold_discount(self, _):
        self.assertEqual(billing.price_for("u1", 1000), 900)

    @mock.patch("billing.get_user", side_effect=KeyError("nobody"))
    def test_guest_pays_list(self, _):
        self.assertEqual(billing.price_for("nobody", 1000), 1000)


if __name__ == "__main__":
    unittest.main()
