import unittest
from datetime import timedelta

from tripbook import itinerary

LEGS = [
    {"depart": "2026-03-05T08:00+07:00", "arrive": "2026-03-05T09:15+07:00", "cost": 1800, "currency": "THB"},
    {"depart": "2026-03-01T09:30+00:00", "arrive": "2026-03-02T04:00+07:00", "cost": 640},
]


class Itinerary(unittest.TestCase):
    def test_legs_come_out_in_departure_order(self):
        self.assertEqual([l["cost"] for l in itinerary.ordered_legs(LEGS)], [640, 1800])

    def test_duration_crosses_zones(self):
        self.assertEqual(itinerary.total_duration(LEGS), timedelta(days=3, hours=16, minutes=45))

    def test_empty_trip_has_no_duration(self):
        self.assertEqual(itinerary.total_duration([]), timedelta(0))

    def test_cost_converts_foreign_legs(self):
        self.assertEqual(itinerary.total_cost(LEGS, {"THB": 0.022}), 679.6)

    def test_unknown_currency_is_an_error(self):
        with self.assertRaises(KeyError):
            itinerary.total_cost(LEGS, {})

    def test_parse_keeps_the_offset(self):
        self.assertEqual(itinerary.parse_time("2026-03-01T09:30+07:00").utcoffset(), timedelta(hours=7))


if __name__ == "__main__":
    unittest.main()
