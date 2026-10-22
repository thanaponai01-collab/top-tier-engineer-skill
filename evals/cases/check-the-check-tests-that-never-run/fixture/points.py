def points_for(order_total, tier):
    """Points earned for one order, per SPEC.md 1-2."""
    base = int(order_total)
    return base * 2 if tier == "silver" else base


def redeem(balance, points):
    """New balance after redeeming `points`, per SPEC.md 3."""
    if points > balance:
        raise ValueError("not enough points")
    return balance - points
