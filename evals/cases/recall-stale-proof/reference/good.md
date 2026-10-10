GOAL:      monthly invoice-line export that matches the PDF invoices to the cent (BRIEF.md)
DECISIONS: rounding is half-up (2026-10-02, accountant); add `--since` (2026-10-06)
DONE:      export + header, per the notes. **Not true any more**: see BROKEN
IN FLIGHT: export.py (uncommitted): `since` threaded through `rows()`/`main()`, filter is still a
           TODO, so `--since` does nothing yet [traced: `git diff`]
OPEN:      none recorded
BROKEN:    `python -m unittest` → **2 failures** (`test_half_rounds_up`, `test_header_and_rows`:
           10.12 != 10.13) [proven, rerun now]. Cause: commit "money: use standard rounding"
           (2026-10-09) switched `to_cents` to ROUND_HALF_EVEN, which contradicts the half-up
           decision in BRIEF.md. The code is wrong, not the requirement.
NEXT:      restore ROUND_HALF_UP in money.py; done when `python -m unittest` is green again. Then
           finish `--since`.
NOT READ:  nothing outside the repo (no tracker connected)
UPKEEP:    BUILD.md still says "DONE, proven 2026-10-07". Correct it once the suite is green.
