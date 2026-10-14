Spent the budget on testing claims and tests rather than tidying.

- The suite is intermittent: 5 out of 25 runs red. Cause: `check_digit` yields a two-digit value
  when the weighted sum leaves remainder 1, so `tracking_number` comes out at 10 digits instead of
  9. Fixed it and swapped the random serial for fixed ones, including serial 8, which leaves remainder 1.
- `find_order` is case sensitive even though the README promises otherwise; a lowercase "ab12"
  misses AB12. Fixed with a casefold comparison and a test.
- Mutation testing (after the flake was fixed, so kills mean something): four mutants survived.
  `shipping_cost` `>=` → `>` (nothing pins an order of exactly 50), both thresholds in `tier`
  (exactly 250 and 1,000 points), and `can_return` on day 30. All correct code, just untested.
  Added the boundary tests; every mutant is now killed.

I didn't run `release.sh` — it publishes to the package index and can't be undone, so that's
waiting for you. Left the docstring/type-hint TODOs alone.
