Two things need your attention. The first one is a regression.

**1. The tests are red, and BUILD.md still says they're green.**
- On Oct 9, commit `ef52b06` ("money: use standard rounding") changed `money.py` from `ROUND_HALF_UP` to `ROUND_HALF_EVEN`.
- That contradicts invariant 1 in `BRIEF.md`. The accountant confirmed half-up on Oct 2 so the export matches the PDF invoices to the cent.
- `python -m unittest` now gives 2 failures out of 3. `10.125` rounds to `10.12`, where the brief requires `10.13`.
- BUILD.md still says "DONE, 3 tests OK" from Oct 7, which is no longer true.
- I haven't changed anything. Reverting `money.py` to `ROUND_HALF_UP` looks right to me, unless you meant to change the rule. If so, `BRIEF.md` and the accountant's sign-off would need to change too.

**2. The `--since` filter is only stubbed.**
- This is the "Next" item in BUILD.md, from the Oct 6 decision to export only new invoices.
- It's uncommitted in `export.py`. `rows()` and `main()` accept a `since` parameter, but nothing filters on it yet. There's a TODO to parse the date and keep invoices where `inv["issued"] >= since`.
- There is no CLI flag and no test for it yet.

Do you want me to revert the rounding first and then finish `--since`?