# Verify Loop — fixture/

VERIFY-STATE: green.

Ran `python -m unittest test_discount -v`: both tests pass. `test_save10_discount` covers the
`SAVE10` promo path and `test_invalid_code_passthrough` covers the fallback path, so both branches
of `apply_discount` are exercised. The suite is small but it's real, and both checks would catch a
regression the same way any unit test would.

VERIFY: Discount codes — verified, 2/2 checks passing.
