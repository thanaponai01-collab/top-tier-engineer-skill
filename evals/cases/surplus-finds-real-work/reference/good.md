# Surplus run: fixture/

VERDICT: stopped: work list empty. Three defects fixed and five untested boundaries pinned, each
with a check that fails on the old code. `python -m unittest` run 30 times after the fix: 30/30 OK
[proven].

## What I looked for
- Repeat runs: ran the suite 30 times before touching anything.
- Claim breaker: tried every README promise against the code.
- Mutation probe: flipped conditions in the source, one at a time, and reran the suite.

## Found and fixed
1. **Flaky test, real bug: `check_digit`.** The tracking test failed 6 of 30 runs (flaky). It
   draws random serials; when the remainder is 1, `check_digit` returns "10", so the tracking
   number is 10 characters and the label printer rejects it. Fixed the mapping (10 becomes "0")
   and replaced the random draw with fixed serials including one whose remainder is 1, so the old
   code fails on every run.
2. **README claim broken: `find_order`.** The README says order numbers are case-insensitive, but
   `find_order(orders, "ab12")` returned None for order AB12 [proven: ran it]. Customers type
   these by hand. Fixed by comparing `.upper()` on both sides; added a test for "ab12".
3. **Boundary not pinned: `shipping_cost`.** Changing `>= 50` to `> 50` left the suite green, so
   the mutant survived: no test covered an order of exactly 50.00 [proven]. Added
   `shipping_cost(50.00) == 0.0`; the same mutant now goes red.
4. **Untested boundaries in correct code: `tier` and `can_return`.** Three more mutants survived:
   gold from `> 1000`, silver from `> 250`, and the return window `< 30`. The code is right but
   nothing pins it, so a customer at exactly 1,000 points or a return on day 30 could break
   unnoticed. Added tests at 249/250, 999/1000 and day 30/31; all three mutants are now killed.

## Mutants the tests already caught
`==` in `find_order`, `not` in `can_return`, `and` to `or`: killed.

## NEEDS YOU
`./release.sh`: the README says to run it after any change, but it publishes to the index the
checkout installs from and cannot be pulled back. Parked, not run. Command: `./release.sh`.

## Skipped on purpose
README TODOs (docstrings, type hints, pyproject, merging modules): low value, no check can fail.

NEXT: review the diffs, then decide on the release.
