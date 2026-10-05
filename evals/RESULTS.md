# Verification workflow evaluation

Follow-up on 2026-10-05: the stricter case requires a frozen baseline and a current,
strict green helper status, alongside broken/correct implementation replays.
One with-skill run passed all gates; one without-skill run failed. The successful
agent repaired the empty check, recorded a behavioral rejection, froze its checks,
fixed refunds and completed strict verification. This is a smoke test, not a
reliability estimate. Phrase grading and artifact checks were used; no semantic judge.

Evidence: `evals/results/2026-10-05-1839/`. Approximate cost: $0.37.
All 326 unit tests pass, including the two reproduced false-green regressions.
The runner now freezes directly named helpers and requires a declared failure signal.
Imported helpers and expectation files still need explicit oracle declarations.

## Earlier evaluation (weaker completion gates)

Targeted evaluation on 2026-10-05 (Asia/Bangkok), using Claude Code's default model
(`claude-sonnet-5-5`). This run used phrase grading (`--no-judge`), action/artifact checks,
and replay of the agent's check against broken and correct implementations. No semantic judge
was run. These are small-sample smoke evaluations, not a reliability estimate.

| Case | Without skill | With skill, grader verdict | Full helper workflow observed |
|---|---|---|---|
| verify-loop-make-it-verified | 0 of 1 | 3 of 5 | 2 of 5 |

The first two skill runs repaired the vacuous check, recorded an actual failure, froze the
checks, fixed the product and ran strict verification/status successfully. The plain run only
diagnosed the problem and asked whether to fix it.

After integrating the upstream document split, run 3 repaired the check and product but skipped
the helper; the case grader passed its outcome because freezing is advisory in that case.
Treat its workflow as incomplete. Run 4 also skipped the helper and omitted the proof note.
The final run (5), with the original detailed steps restored and helper location explicit,
ran helper help and exposed the faulty check, but stopped before the product fix and final loop.
It asked for permission despite the task requesting verified refunds.

**Final limitation:** the verifier's executable checks pass, but the final live skill evaluation
does not establish reliable autonomous completion. Preserve this limitation rather than infer
reliability from the earlier successful runs. The final merged code passed all 323 unit tests.

- Raw evidence: `evals/results/2026-10-05-1741/` (reports, action logs, grades and results).
- Total evaluation cost: approximately $1.22.
- Plugin version evaluated: 4.49.0.
- Every with-skill run loaded the skill; transcripts stay local per .gitignore.

Reproduce with `python evals/run.py --cases verify-loop-make-it-verified --repeats 1`.
