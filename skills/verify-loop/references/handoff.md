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
  | latent-audit | the deleted candidate still reached by a caller, or dead code unflagged |
  | structure-gate | a structural breach or complexity exceeding baseline threshold |
  | agent-drift | the diverged input reproducing a below-band score |
  | senior-review | the observed breakage or boundary gap reproduced |

- **Adjacent regressions**: callers of what changed, which must stay green.

## This skill does

Records the sections in VERIFY.md (or composes via `include:` in monorepos), retains the rejection receipt,
freezes with `baseline`, and finishes with `run --strict` (or `run --affected` during fast-feedback iterations) and
`status`, as in the loop. If checks were repaired, it collects fresh rejection evidence; it never changes an
expected result to match the fix.

Rules that hold for every caller:

- Read this skill's SKILL.md and VERIFY_FORMAT.md, and run its bundled helper from the installed
  skill location, never an assumed path in the target repo.
- The rejection must be the behavioral `fail-signal:`. A missing dependency, startup failure or
  timeout proves nothing.
- Controlled mutations run in scratch copies, with fake accounts and data. Never break a live
  system to prove a check can fail.
- Record the conditions the result depends on (environment, target identity, workload) in the
  retained evidence. Keep secrets out of captured output.
- Keep prior mapped behavior green and report what stays unmapped.

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
