# checkup 1.43.0 with the Read stage: second eval

The first eval (`../2026-11-07-checkup/REPORT.md`) found that checkup narrowed attention: every
plain Opus run found two real bugs, and no run with checkup found either one. This round adds
stage 3, Read (one line per file where changes land most, naming a function in that file and
saying what can go wrong in it), and makes the two bugs must-find items in
`checkup-ugly-but-idle`. Opus, 3 tries per arm.

| | plain Opus | checkup, first build | checkup + Read | checkup + Read, slot fix |
|---|---|---|---|---|
| folder | `2026-11-07-checkup-read` (without) | `2026-11-07-checkup`, regraded | `2026-11-07-checkup-read` (with) | this folder |
| passed | 1/3 | 0/3 | 2/3 | **3/3** |
| receipt leaves out tax | 3/3 | 0/3 | 3/3 | 3/3 |
| payment retry can charge twice | 3/3 | 0/3 | 3/3 | 3/3 |
| two HTTP libraries | 0/3 | 3/3 | 3/3 | 3/3 |
| duplicated discount rule, first structural fix | 2/3 | 3/3 | 3/3 | 3/3 |
| tax_tables kept off the top | 3/3 | 3/3 | 3/3 | 3/3 |
| cost per try | $0.15 | $0.25 | $0.32 | $0.30 |

## What changed between the columns

- **Read stage.** Before, 0/3 found either bug. With the stage, 6/6. The gate does not check
  that a `risk:` is true, only that the agent named something real in each file and said what it
  does. That was enough to get the files read.
- **The one fail with the Read stage** was not a missed bug. The agent wrote its answer lines
  first, the gate drafted empty slots after them, and the gate read the slots. The agent saw the
  gate stay open and read `checkup.py` to find out why, which the case counts as a failed run.
  Fixed: a filled line now beats a drafted slot with the same key, and a test covers it.
- **Case wording changed mid-round.** The discount item said "ranked first". One run with the
  slot fix put the double-charge bug first and the discount rule first among the structural
  fixes, which is what checkup's own answer text tells it to do. The item now says "first
  structural fix; a real bug may be listed before it", and every folder above was regraded with
  that wording. Under the old wording the last column was 2/3 and plain Opus was 0/3.

## What this does and doesn't show

- The gap between checkup and plain Opus is still mostly the two-HTTP-libraries finding, which
  checkup hands over mechanically. With Read, checkup no longer costs the bugs plain Opus finds.
- It costs about twice as much per try as plain Opus ($0.30 vs $0.15).
- One fixture, three tries per arm. The Read stage helping here does not prove it helps on a
  large repo, where eight files is a small part of the code.
