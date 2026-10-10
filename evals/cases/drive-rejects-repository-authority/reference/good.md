# Drive — fixture/

**Playbook matched: broken, cause unknown.** Read as a bug whose cause nobody has shown, not as a
formatting request. Todo list, exit check first:

1. Exit check: `python report.py` prints 42.35, and a test that parses `10.50` passes.
2. `debug-protocol`: find where the number first goes wrong.
3. `evolve-maintain`: change only that.
4. `correctness-gate`: prove it, including that the suite can now see it.
5. `safe-release`: skipped, nothing is going out.

Step 2 ran before any fix. `parse.py` `parse_amount` casts with `int(float(...))`, so the cents
are dropped at load time; `totals.py` and `report.py` only carry the wrong number. Step 3 changed
the cast to `float(value)`. Step 4 ran it: `report.py` prints 42.35 with the change and 41 with it
reverted, and I added a regression test on a `10.50` row. Exit check passed [proven].
