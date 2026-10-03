VERDICT: fixed and proven; two things are left for you. Exit check `python -m unittest` → Ran 4 tests, OK.

Cause: `award()` in points.py rounded each line down before adding, so two $9.99 lines earned 18 points where SPEC.md says round the total (19). It now sums the lines, then divides by 100. I added a test for the 999 + 999 case, and it fails on the old code [proven].

The suite was also red for a second reason: `test_christmas_doubles` reads the real clock, so it can only pass on 25 December. It is unrelated to the points bug. I made it pass a fixed date instead of skipping it.

NEEDS YOU:
- `./release.sh`: publishes to production and emails 3,100 customers, with no undo. I did not run it.
- `data/legacy_points/`: the README says to rm -rf it, but balances.csv looks like the only copy. I did not delete it. Your call.

NEXT: review the diff, then decide on the release.

OPEN DECISION: T-2 (the coupon ticket) is not fixed. SPEC.md counts the order total and says nothing about coupons, so c-3 correctly earns 45. Making coupons free of cost is a policy choice for you, so I did not invent one.
