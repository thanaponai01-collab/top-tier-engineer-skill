from datetime import date

LATE_FEE_RATE = 0.05


def late_fee(due: date, paid: date, amount: float) -> float:
    """Fee for paying `amount` on `paid` when it was due on `due`. Paying on the due date is on time."""
    if paid > due:
        return round(amount * LATE_FEE_RATE, 2)
    return 0.0


def invoice_total(amount: float, due: date, paid: date) -> float:
    """What the customer owes: the amount plus any late fee."""
    return round(amount + late_fee(due, paid, amount), 2)
