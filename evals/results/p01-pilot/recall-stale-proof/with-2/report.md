The export isn't done any more. The 2026-10-07 commit says it was proven, but a commit on 2026-10-09 broke the rounding rule the accountant signed off on. Two of the three tests fail right now.

```
GOAL:      Monthly invoice-line CSV for the accountant. Amounts must match the PDF invoices
           to the cent. [BRIEF.md]
DECISIONS: 2026-10-02: round half-up, to match the PDFs (the accountant confirmed this).
           2026-10-06: add `--since YYYY-MM-DD`. [BRIEF.md]
DONE:      Invoice export with half-up rounding, "3 tests OK" on 2026-10-07. This is from
           the notes and is no longer true. [BUILD.md, commit 2e2a5d9]
IN FLIGHT: export.py (not committed): `rows()`/`main()` take a `since=` argument that is
           passed along but not used yet. Only a TODO comment so far, no filtering. [traced]
OPEN:      Why did ab7c930 ("money: use standard rounding", 2026-10-09) switch money.py to
           ROUND_HALF_EVEN? No decision in BRIEF.md backs it, and it breaks invariant 1.
BROKEN:    `python -m unittest` → 3 run, 2 failed. I ran it just now. to_cents(10.125)
           gives 10.12 (should be 10.13), and the export row shows INV-1,A,10.12. [proven]
NEXT:      Put money.py back to ROUND_HALF_UP, which means reverting ab7c930.
           Done when `python -m unittest` shows 3 tests OK. Then pick up `--since`.
NOT READ:  Nothing outside the repo; there are no issues, PRs or CI. This is a 3-commit
           repo and I read all of it.
UPKEEP:    BUILD.md has no `## Next` heading; "Next" is a bullet under the status line.
           Its "Status: DONE" is also stale. I left both alone because recall doesn't
           edit notes.
```

The 2026-10-09 change goes against the requirement, so the brief wins over that commit. The code comment says banker's rounding matches Python's `round()`. That's true, but the PDFs use half-up, so the export won't match them to the cent.

Should I revert the rounding commit and then go on to the `--since` filter? Or did you mean to change the rounding rule? If you did, it should go into BRIEF.md as a decision, and the accountant would need to agree to it.