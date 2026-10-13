Short version: the export is **not done any more**. Since you last ran it green, a commit switched the rounding rule and 2 of the 3 tests now fail.

```
GOAL:      Monthly CSV export of invoice lines whose amounts match the PDF invoices to the cent.  [BRIEF.md]
DECISIONS: 2026-10-02 rounding is half-up (10.125 -> 10.13), confirmed by the accountant.
           2026-10-06 add `--since YYYY-MM-DD` so each monthly run exports only new invoices.  [BRIEF.md]
DONE:      Invoice export, "3 tests OK" on 2026-10-07 (from the notes: BUILD.md, commit 2e2a5d9).
           That is no longer true: the tests fail now (see BROKEN).
IN FLIGHT: export.py, not committed: `since=` added to rows()/main() and passed through, but the filter
           itself is only a TODO comment ("filter on inv["issued"] >= since; parse the date first").
           Right now `since` does nothing. No test, no CLI flag.  [traced]
OPEN:      Why was ab7c930 "money: use standard rounding" (2026-10-09) made? It switched
           ROUND_HALF_UP to ROUND_HALF_EVEN, which breaks invariant 1 and the accountant's decision.
           No note or decision records the change.
BROKEN:    `python -m unittest` -> FAILED (failures=2), run now. test_half_rounds_up: 10.12 != 10.13;
           test_header_and_rows: INV-1,A,10.12 vs 10.13. Cause: money.py:7 (ROUND_HALF_EVEN). [proven]
           The uncommitted diff doesn't touch rounding, so it isn't the cause.  [traced]
NEXT:      Put ROUND_HALF_UP back in money.py, as BRIEF requires. Done when `python -m unittest`
           shows 3 OK again. Then pick up --since.
NOT READ:  No issues, PRs or CI checked (no tracker connected). No memory directory. The whole repo
           is the 6 files above, and I read all of them.
UPKEEP:    BUILD.md puts "Next" in a bullet, not a `## Next` section, so the handoff check flags it.
           Also, its "Status: DONE" is out of date until rounding is fixed.
```

The 10-09 commit looks like an attempt to use "standard" rounding that didn't know about the accountant's half-up requirement. If you made that switch on purpose (the accountant changed the rule, say), tell me. That's a new decision: I'd record it in BRIEF.md and update the tests instead of reverting the code. Otherwise, should I revert the rounding and then build the `--since` filter?