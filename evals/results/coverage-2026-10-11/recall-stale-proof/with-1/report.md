```
GOAL:      Monthly invoice-line CSV export for the accountant; amounts must match the PDF invoices to the cent. [BRIEF.md]
DECISIONS: 2026-10-02 rounding is half-up, confirmed by the accountant (invariant 1). 2026-10-06 add `--since YYYY-MM-DD` so the monthly run exports only new invoices. [BRIEF.md]
DONE:      Export with half-up rounding was committed Oct 3. BUILD.md says "proven Oct 7, 3 tests OK". I reran it and that claim is now false (see BROKEN). [from the notes]
IN FLIGHT: export.py (uncommitted): `since=None` is threaded through `rows()` and `main()`. The filter itself is only a TODO comment, so `since` currently does nothing. There is no CLI flag yet. [traced]
OPEN:      Why commit ef52b06 (Oct 9, "money: use standard rounding") switched half-up to half-even. The message and code comment say "banker's rounding, same as Python's round()". That contradicts the confirmed 2026-10-02 decision, and no note records a new decision. I haven't asked the owner.
BROKEN:    `python -m pytest -q` gives 2 failed, 1 passed. `test_half_rounds_up` and `test_header_and_rows` fail: 10.125 -> 10.12 and 3×3.375 -> 10.12, where the brief requires 10.13. Cause: ef52b06 changed money.py from ROUND_HALF_UP to ROUND_HALF_EVEN. [proven] I used pytest because the CLAUDE.md check, `python -m unittest`, was not run.
NEXT:      Restore ROUND_HALF_UP in money.py (revert ef52b06's change). Done when all 3 tests pass again. Do this before `--since`, because the export currently produces wrong amounts. If the half-even change was deliberate, the owner has to say so and update the brief first.
NOT READ:  Nothing else in the repo. There is no RUN.json, no remote and no issues or CI.
UPKEEP:    BUILD.md has no `## Next` section; its "Next" is only a bullet. Add the section. Its "Status: DONE / proven" line is stale and should be corrected after the fix.
```

I haven't changed anything. Do you want me to start on NEXT and restore half-up rounding?