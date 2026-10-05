# Handoff from another skill

A specialist skill knows what is wrong; this skill keeps the proof that the check would catch it.
Use this contract when a skill hands work here, so each caller states only its own part.

## When a handoff applies

The project has a VERIFY.md, or the user asked for reusable verification. Otherwise the caller
runs its checks directly. A diagnosis, review or readiness request ends with the caller's findings
and a proposed runnable check; strict green is not its completion gate.

## The caller supplies

- **The claim**, in observable terms.
- **Where the expected result comes from**: spec, policy, contract or budget. Never the code.
- **The real-run command** that watches the behavior.
- **The wrong state the check must reject.** This becomes the step-4 rejection, or a
  `verify.py challenge` mutation run in a scratch copy:

  | Caller | Wrong state |
  |---|---|
  | debug-protocol | the proven cause, reintroduced |
  | correctness-gate | a mutation of the boundary or rule |
  | threat-model | the abuse request, which must be refused |
  | perf-optimize | the slow path, which must exceed the budget |
  | wire-check | the connection removed, which must break the entry point |
  | safe-release | the change missing on the target, or the rollback not restoring data |
  | build-discipline, evolve-maintain | the slice's behavior absent, or the old behavior broken |

- **Adjacent regressions**: callers of what changed, which must stay green.

## This skill does

Records the sections in VERIFY.md, retains the rejection receipt, freezes with `baseline`, and
finishes with `run --strict` and `status`, as in the loop. If checks were repaired, it collects
fresh rejection evidence; it never changes an expected result to match the fix.

## The caller keeps

Its own verdict: oracle quality and mutation breadth, severity, the performance baseline (kept
separate from the check baseline), go/no-go. A green recipe covers the mapped claims only.

## What comes back

The `VERIFY:` summary line and `VERIFY-STATE: green` (or the state it is in), the observed
rejection, and the gaps. Drive, RUN.json and release gates read these.

## When this skill is not installed

Look in the installed plugin's sibling skills and the available skill catalog first. If it is
truly absent, run the same check directly before and after, keep both outputs, and say that
reusable strict evidence is missing.
