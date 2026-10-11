```
GOAL:      Monthly invoice-line CSV export that matches the PDF invoices to the cent. [BRIEF.md]
DECISIONS: Amounts are rounded half-up (10.125 → 10.13), confirmed by the accountant on 2026-10-02.
           Add `--since YYYY-MM-DD` so the monthly run exports only new invoices (2026-10-06). [BRIEF.md]
DONE:      Header row and the `--since` signature only. The export itself is NOT done any more. [proven, reran now]
IN FLIGHT: export.py (uncommitted): `rows()`/`main()` accept `since`, but the filter is only a
           TODO comment, so nothing gets filtered and `since` is ignored. There are no tests for it. [traced]
OPEN:      Who made the 2026-10-09 rounding change, and why? Nothing records a decision to change the rule.
           Also: what format is `inv["issued"]` in? The TODO says "parse the date first".
BROKEN:    `python -m unittest` → 2 of 3 tests FAIL (10.12 != 10.13). Commit ab7c930 "money: use standard
           rounding" (Oct 9) switched money.py from ROUND_HALF_UP to ROUND_HALF_EVEN. That breaks
           BRIEF invariant 1 and would make the export disagree with the PDFs. BUILD.md still says
           "DONE, 3 tests OK" (Oct 7), which is now out of date. [proven]
NEXT:      Put `to_cents` back to ROUND_HALF_UP, unless you're deliberately changing the accountant-confirmed
           rule. Done when `python -m unittest` → 3 tests OK.
NOT READ:  No remote, issues or CI exist. My memory directory is empty. History before 0e5cb8f is not
           relevant (only 3 commits in total).
UPKEEP:    BUILD.md has "Next:" as a bullet rather than a `## Next` heading, so the handoff check flags it.
           The Status line needs updating to match reality.
```

**Where we were:** the export shipped on Oct 7 with the tests passing. You'd started the `--since` filter, which is in the uncommitted changes to `export.py`. Then on Oct 9 a commit switched rounding to banker's rounding. That silently broke the half-up rule the accountant confirmed, and the notes still say everything is green.

I haven't changed anything. Do you want me to revert the rounding and then finish `--since`? Or was the switch to half-even on purpose? If it was, that's a change to the brief and needs the accountant's agreement first.