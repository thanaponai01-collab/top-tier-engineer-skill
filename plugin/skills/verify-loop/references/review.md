# Review a change by proof

Use when asked to review a PR, a branch, a commit or another agent's work, or to judge whether a
change is proven. The output is findings a person can re-run, not opinions. This mode reads: it
records no state or receipts and edits nothing.

```bash
python <skill-base>/scripts/verify.py review . [--base REF] [--no-mutate] [--jobs N] [--max N] [--json]
```

`--base` is the commit the change is measured from: `HEAD` (default) for uncommitted work, the PR's
base branch for a PR (`--base origin/main`). Uncommitted and untracked files count as part of the change.

| Severity | Finding | Meaning |
|---|---|---|
| high | `TEST REMOVED` / `TEST SKIPPED` / `TEST WEAKENED` / `TEST HOLLOWED` | A test function that existed at the base is gone, newly skipped, has fewer assertions, or can no longer fail. Renamed files are compared, not reported as removed |
| high | `CHECK REMOVED` / `SIGNAL CHANGED` / `FEATURE REMOVED` / `REQUIREMENT REMOVED` | VERIFY.md lost or edited a check, a fail-signal, a feature or a `require:` word |
| high | `ORACLE CHANGED` / `CHECK CHANGED` | Expected data or a check script was edited in the same change as the code it judges |
| medium | `UNCOVERED` | A changed line no check reaches: an abort placed there still passes |
| medium | `SURVIVED` | A mutant of a changed line that every check lets through |
| medium | `UNMAPPED` | A changed product file no feature names, and the survey did not judge it |
| medium | `NOT SURVEYED` | No VERIFY.md, or the mutation survey could not run (for example the checks are red before mutation) |

Exit 0: no findings. Exit 1: findings. Exit 2: cannot review (not a git repo, unknown base).

The mutation part is the `swarm --auto --diff` survey, with each mutant judged against **every**
feature's checks: it counts as caught when any check catches it. Each `SURVIVED` or `UNCOVERED`
finding carries a `reproduce:` command, a single `challenge` a person can run to see it.
`--no-mutate` gives the static findings in well under a second.

## Reading the findings

A high finding is not proof of cheating. Removing a test can be right, for example when the
feature was removed too. It is something the author must explain, and the reviewer must not
assume it was fine. Give the reason in the review, or ask for it.

A medium finding is a missing proof, not a bug. The fix is a spec-backed check (see
[challenge](challenge.md)), never a check copied from the implementation's own output.

`VERIFY-STATE:` at the end is the last recorded verdict, not a fresh run. When the review must also
say the change is green, run `run --strict` and `status` after it, or let [CI](ci.md) do it.

## Who runs it

A review is the judge's role. Run it in a context that did not write the change: a subagent, a
second `VERIFY_AGENT`, or CI. An author who reviews their own change gets the same findings, but
they explain away their own high findings more easily. Clean review output means only that no
listed finding applies. It does not mean the change is correct: what the change should have
tested but didn't is still for the reviewer to read for.
