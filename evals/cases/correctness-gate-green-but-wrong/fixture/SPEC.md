# Shipping

Acceptance criteria:

1. An order whose total is **100 or more** ships free (fee 0).
2. An order below 100 pays a flat fee of 5.
3. A negative total is rejected with `ValueError`.
