Short version: you were partway through the `--since` filter, but something bigger needs fixing first. The Oct 9 commit switched rounding to banker's rounding, which breaks the owner's half-up rule, and 2 of the 3 tests now fail.

```
GOAL:      Monthly invoice-line CSV for the accountant that matches the PDF invoices to the cent. [BRIEF.md]
DECISIONS: (1) Round half-up, 10.125 -> 10.13, confirmed by the accountant 2026-10-02.
           (2) Add `--since YYYY-MM-DD` so the monthly run exports only new invoices, 2026-10-06. [BRIEF.md]
DONE:      Invoice export with half-up rounding (0e5cb8f, Oct 3). BUILD.md says "DONE, 3 tests OK on 2026-10-07".
           That's from the notes and no longer true (see BROKEN).
IN FLIGHT: export.py (uncommitted): `since=None` is passed through main() -> rows(), but the filter isn't
           there yet. Only a TODO: filter on inv["issued"] >= since, parse the date first. No tests. [traced]
OPEN:      Was ab7c930 "money: use standard rounding" (Oct 9) on purpose? It switched to ROUND_HALF_EVEN,
           which goes against BRIEF invariant 1 and the accountant's decision. Nothing records a change of mind.
BROKEN:    `python -m unittest` -> FAILED (failures=2) [proven, just now]
           test_half_rounds_up: 10.12 != 10.13 · test_header_and_rows: INV-1,A,10.12 != 10.13
NEXT:      Put ROUND_HALF_UP back in money.py, unless the accountant has changed the rule.
           Done when `python -m unittest` -> 3 tests OK. After that, finish `--since` with a test.
NOT READ:  No remote, issues or CI. Only branch is `main`. Nothing stashed. I read the whole repo (6 files).
UPKEEP:    BUILD.md has "Next" as a bullet, not a `## Next` heading, so the handoff check flags it as missing.
           Its "Status: DONE" is also stale while the tests fail.
```

What I found:
- **The rounding change is a real money error.** The export now differs from the PDF invoices whenever a line lands exactly on a half cent. The commit message calls it "standard rounding", but the brief says half-up is required and the accountant confirmed it.
- **The `--since` work is safe to leave for now.** It only adds plumbing; the filter itself isn't written. None of the test failures come from it.

I haven't changed anything. Did you mean to switch to banker's rounding? If not, I'll revert `money.py` and confirm the tests pass. If you did, the brief needs updating first, because the accountant signed off on half-up. Then the tests would be updated to match.