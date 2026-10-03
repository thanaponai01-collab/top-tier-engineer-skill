import datetime
import unittest

from points import award, holiday_multiplier


class Points(unittest.TestCase):
    def test_whole_dollars(self):
        self.assertEqual(award({"lines": [(2, 2500)]}), 50)

    def test_christmas_doubles(self):
        # passes only on 25 December: reads the real clock
        self.assertEqual(holiday_multiplier(), 2)

    def test_ordinary_day_is_single(self):
        self.assertEqual(holiday_multiplier(datetime.date(2026, 3, 3)), 1)


if __name__ == "__main__":
    unittest.main()
