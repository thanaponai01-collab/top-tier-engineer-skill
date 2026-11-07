# checkup 1.43.0: first eval

Case `checkup-ugly-but-idle`, 3 tries per arm, claude-opus-5-5, $1.18 in all. Scorecard:
`RESULTS.md`; every report, transcript and grade is under `checkup-ugly-but-idle/`.

| | plain Opus | with checkup |
|---|---|---|
| passed (all three planted, no trap) | 0/3 | 3/3 |
| cart + receipt rule ranked first | 2/3 | 3/3 |
| two HTTP libraries named | 0/3 | 3/3 |
| tax_tables (ugly, idle) kept off the top | 3/3 | 3/3 |
| cost · time · turns per try | $0.15 · 37s · 4 | $0.25 · 56s · 9 |

## What the numbers do and don't say

- The trap the case was built around did not catch plain Opus. All three plain runs read the git
  history and said `tax_tables.py` looks worst but has not changed since the first commit. The
  ranking idea was not the gap.
- The gap is the HTTP finding, and checkup hands it over mechanically (dep-map's I/O imports
  grouped by job). Plain Opus did talk about the retry loops, but as a payments problem, not as
  two clients.
- **The skill arm missed two real bugs every plain run found.** Neither was planted on purpose,
  so the grader does not count them:
  - the receipt total leaves out tax, while checkout charges cart total plus tax
    (`shop/checkout.py`, `shop/receipt.py`): customers see a different amount from what they paid;
  - `shop/payments.py` retries `POST /charge` on timeouts and 502/503 with no idempotency key, so
    one order can be charged more than once.
  The with-skill reports stayed inside the eight sections. Two of them said "no third fix is
  earned yet" with a double-charge bug in the code.

So: on what the case measures, the skill helps (3/3 vs 0/3). Across everything a user would want
to hear, the plain runs were more useful on this fixture. The skill narrows attention to what its
helpers measure.

## Next

- Close the narrowing with a gate, not advice: for example a stage that needs one line per file
  the agent read but no section flagged, saying what it found there or `nothing`, so reading the
  code is checked before the answer is given.
- Plant the two accidental bugs on purpose in this case (as must-find items), so the grader holds
  the skill to them.
