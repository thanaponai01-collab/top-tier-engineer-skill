import unittest

from app import money


class Money(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(money.parse_amount("12.34"), 1234)
        self.assertEqual(money.parse_amount("-5"), -500)
        self.assertEqual(money.parse_amount("$1,200.5"), 120050)

    def test_format(self):
        self.assertEqual(money.format_money(1234), "$12.34")
        self.assertEqual(money.format_money(-1064), "-$10.64")
