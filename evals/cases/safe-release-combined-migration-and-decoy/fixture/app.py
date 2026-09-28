def order_total_display(row):
    """row is the orders row after migration 002 has run — reads total_cents directly.

    Deployed in the same release as migration 002, so the read switch and the
    column drop go out together.
    """
    return f"${row['total_cents'] / 100:.2f}"
