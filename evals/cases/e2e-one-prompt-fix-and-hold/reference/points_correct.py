"""Loyalty points. Spec (SPEC.md): 1 point per whole dollar of the order TOTAL, rounded down."""
import datetime


def points_for_total(total_cents):
    return total_cents // 100


def award(order):
    return points_for_total(sum(qty * unit_cents for qty, unit_cents in order["lines"]))


def holiday_multiplier(today=None):
    today = today or datetime.date.today()
    return 2 if (today.month, today.day) == (12, 25) else 1
