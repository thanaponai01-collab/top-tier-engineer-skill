"""Checkout pricing."""
from users import get_user

DISCOUNT = {"gold": 0.10, "silver": 0.05}


def price_for(user_id, amount_cents):
    """Members get their tier discount; anyone we can't find pays list price."""
    try:
        tier = get_user(user_id)["tier"]
    except KeyError:
        return amount_cents
    return round(amount_cents * (1 - DISCOUNT.get(tier, 0)))
