The biggest gap is `split_payment`. An outside team could change it to lose cents and the gate would still pass all 29 tests. I checked this by applying each change to a copy of `billing.py` and running the suite against it.

**1. Splitting a payment can drop money. All 29 tests pass.**
If someone changes the code to give every card the same amount (`return [base] * ways`), then `split_payment(100, 3)` returns `[33, 33, 33]`. That adds up to 99, so a cent goes missing on every uneven split. SPEC rule 6 says the parts "always add up to the total", but every split the tests use comes out even (9000/3, 12000/4, 4321/1). The remainder code (`base + 1 if i < extra`) does run, but never with a remainder above zero, so the coverage report can't show the problem.

The same blind spot lets a second bug through: putting the extra cents on the last cards instead of the first ones also passes all 29 tests. That breaks the rule that "the first parts carry the extra cents."

**2. The 20-seat discount tier can move. All 29 tests pass.**
If the tier starts at 21 seats instead of 20, a 20-seat team customer pays 2755 per seat (5% off) instead of 2610 (10% off). The tests check exactly 10 and 50 seats, but for the middle tier they only check 25 and 49, never exactly 20. (Changing every `>=` to `>` is caught, because the 10- and 50-seat tests fail. Only the 20-seat boundary is unprotected.)

**Smaller gaps:** these are cases with no test that I didn't run against changed code:
- An annual invoice with credit applied (`invoice(..., annual=True, credit=...)`).
- Credit exactly equal to the amount owed.
- Late interest on the first day after the grace period with a round amount, and a multi-day case where rounding down matters. Only `1999, 8` checks rounding.

**Tests to add before handing it over:**
```python
def test_uneven_split_first_cards_get_extra(self):
    self.assertEqual(split_payment(100, 3), [34, 33, 33])

def test_twenty_seats_get_ten_percent(self):
    self.assertEqual(seat_price("team", 20), 2610)
    self.assertEqual(seat_price("team", 19), 2755)
```

The general lesson: "every statement runs" doesn't mean every branch or boundary is checked. Both bugs sit in code that runs during the tests, just never with inputs that would expose them. Running a mutation-testing tool (e.g. `mutmut`) on `billing.py` would find any others in the same way.