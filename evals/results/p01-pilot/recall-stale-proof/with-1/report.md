Last time you were starting the `--since` filter. Before you go on, there's a problem: a commit on Oct 9 broke the main rounding rule, and 2 of the 3 tests fail right now.

```
GOAL:      Monthly CSV export of invoice lines that matches the PDF invoices to the cent. [BRIEF.md]
DECISIONS: Rounding is half-up (10.125 -> 10.13), confirmed by the accountant on 2026-10-02.
           Add a `--since YYYY-MM-DD` filter (2026-10-06). [BRIEF.md]
DONE:      Invoice export, from the notes: "Proven 2026-10-07, 3 tests OK" [BUILD.md]. That is no
           longer true: I ran the tests now and 2 of 3 fail (see BROKEN).
IN FLIGHT: export.py (not committed): a `since=None` argument is passed from main() into rows(),
           but nothing filters on it yet, only a TODO to compare inv["issued"]. No tests for it. [traced]
OPEN:      Why was the rounding changed? The Oct 9 commit message gives no reason and the brief
           records no new decision.
BROKEN:    Commit ab7c930 ("money: use standard rounding", 2026-10-09) switched money.py to
           ROUND_HALF_EVEN, which turns 10.125 into 10.12. That contradicts the accountant's
           half-up rule. `python -m unittest` -> FAILED (failures=2): test_half_rounds_up and
           test_header_and_rows. [proven, run just now]
NEXT:      Put money.py back to ROUND_HALF_UP (revert ab7c930), and leave the export.py changes
           alone. Done when `python -m unittest` shows 3 tests OK. Then go back to --since.
NOT READ:  Nothing; there are 6 small files and 3 commits on main. No issue tracker or CI is connected.
UPKEEP:    BUILD.md has its next step as a "- Next:" bullet. The project's notes check expects a
           `## Next` section, so turn the bullet into one. Also change Status from DONE, because
           the tests now fail.
```

I haven't changed anything. If the switch to half-even was deliberate, it needs a new decision from the accountant in BRIEF.md, because the PDF invoices still round half-up. Otherwise I'd revert it. Should I go ahead with the revert?