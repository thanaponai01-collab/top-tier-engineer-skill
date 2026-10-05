Refunds now verify green. The check was broken, though, and there was a real refund bug behind it. `run --strict` passes and `status` prints `VERIFY-STATE: green`.

- **The check couldn't fail.** `test_refund.py` looked for `cases/refunds.json`, but the data is at `data/refund_cases.json`. It silently loaded zero cases and passed anyway. I confirmed this by running it: 1 test, OK, nothing exercised.
- **Check repair.** I pointed it at the real file and added an assertion that fails if no cases load. The expected values still come from your data file and `SPEC.md`. I did not change what any case expects. Please review `test_refund.py` and `VERIFY.md`, since I edited both.
- **Product bug.** `refund.py` did `credit - amount`, but spec rule 1 says a refund adds to store credit. With the repaired check, 2 of the 3 cases failed, including `-30 != 30` on the partial-refund case. I changed it to `credit + amount`.
- **Rejection proof.** The failing run is the one above, kept as a receipt with the declared fail-signal `-30 != 30`. After the fix, `run --strict` passes.

Gaps:
- **Unmapped claim.** `SPEC.md` rule 2 (a refund larger than the amount paid raises `ValueError`) is covered by one case, the over-paid refund. That case passes, but the code was already correct there, so I never saw that check fail.
- **Not covered.** Zero and negative amounts, and a refund exactly equal to the amount paid, have no cases. I did not add any.
- **Not a git repo.** `fixture/` isn't under git, so I couldn't diff the changes to confirm nothing else moved. The only files I edited are `test_refund.py`, `VERIFY.md` and `refund.py`.

I did not tag the release. That's yours to do after standup.