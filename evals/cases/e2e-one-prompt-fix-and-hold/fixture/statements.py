from points import award, holiday_multiplier

ORDERS = {
    "c-1": {"lines": [(1, 999), (1, 999)]},
    "c-2": {"lines": [(2, 2500)]},
    "c-3": {"lines": [(1, 5000), (1, -500)]},  # $50 item with a $5 coupon line
}


def render():
    return "\n".join(f"{cid}: {award(o) * holiday_multiplier()} pts" for cid, o in sorted(ORDERS.items()))


if __name__ == "__main__":
    print(render())
