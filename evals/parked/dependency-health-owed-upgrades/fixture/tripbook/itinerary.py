"""Pure trip arithmetic: no third-party packages, so it is what the tests cover."""
from datetime import datetime, timedelta


def parse_time(text):
    """'2026-03-01T09:30+07:00' -> aware datetime."""
    return datetime.fromisoformat(text)


def ordered_legs(legs):
    return sorted(legs, key=lambda leg: parse_time(leg["depart"]))


def total_duration(legs):
    if not legs:
        return timedelta(0)
    ordered = ordered_legs(legs)
    return parse_time(ordered[-1]["arrive"]) - parse_time(ordered[0]["depart"])


def total_cost(legs, rate_to_home):
    """Sum leg costs converted to the home currency; a leg in an unknown currency is an error."""
    total = 0.0
    for leg in legs:
        cur = leg.get("currency", "home")
        if cur == "home":
            total += leg["cost"]
        elif cur in rate_to_home:
            total += leg["cost"] * rate_to_home[cur]
        else:
            raise KeyError(f"no rate for {cur}")
    return round(total, 2)
