"""Shared customers for the points tests."""


class PointsFixtures:
    def setUp(self):
        self.regular = {"tier": "regular", "balance": 120}
        self.gold = {"tier": "gold", "balance": 900}
