"""Monthly statements. Amounts are integer cents throughout."""

CUSTOMERS = {
    "c-101": {"discount_pct": 10, "lines": [(2, 1250), (1, 4999)]},
    "c-102": {"discount_pct": 0, "lines": [(3, 800)]},
    "c-103": {"discount_pct": 5, "lines": [(1, 12000), (4, 350)]},
}


def subtotal(lines):
    return sum(qty * unit_cents for qty, unit_cents in lines)


def discount(amount_cents, pct):
    return amount_cents * pct // 10


def statement_total(customer):
    amount = subtotal(customer["lines"])
    return amount - discount(amount, customer["discount_pct"])


def render():
    return "\n".join(
        f"{cid}: {statement_total(c) / 100:.2f}" for cid, c in sorted(CUSTOMERS.items())
    )


if __name__ == "__main__":
    print(render())
