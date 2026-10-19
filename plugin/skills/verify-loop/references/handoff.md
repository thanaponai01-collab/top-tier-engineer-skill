# Handoff from another skill

A specialist skill knows what is wrong; this skill keeps the proof that the check would catch it.
Use this contract when a skill hands work here, so each caller states only its own part.

## When a handoff applies

For an authorized repair or reusable proof, hand off when VERIFY.md covers the claim or the
user requests a reusable recipe. Otherwise run the scoped checks directly. An assessment
reports actual results, gaps and a runnable check; failure remains a valid verdict and does not
authorize product repairs. Explicit verification/readiness claims still need the proof their
caller requires. Reuse current receipts for unchanged claims and inputs; load this skill only
when proof is missing/stale or checks need work, not because VERIFY.md exists somewhere.

## The caller supplies

- **Scope and authority:** assessment, recipe preparation, or authorized repair; affected paths.
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
  | project-foundation | selected requirement-backed behavior broken in scratch |
  | agent-release | a disabled kill switch, cap or redaction control in scratch |

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

Every caller gets the same answer, whether it is a person, a skill, an agent or another AI. Put
the verdict first:

| Verdict | Meaning |
|---|---|
| `green` | the last whole run was strict and green, and the inputs have not changed since |
| `red` | a check failed, a frozen check or oracle changed, or an edit went outside the scope |
| `partial` | the run was green but not strict, so rejection proof or the baseline was not required |
| `stale` | files changed after the last green run |
| `unverified` | no VERIFY.md, or no whole run recorded |

Then:

1. **The `VERIFY:` line** from the last whole run.
2. **The observed rejection:** for each proven feature, which check went red, on which wrong state
   (its `fail-proof:`), with which `fail-signal:`, and the output line that was seen.
3. **What passed:** the feature and the command, for each check.
4. **Gaps:** failing checks, features with no check, features never seen red, orphan tests and
   blind spots. Then whatever green cannot show, such as features nobody mapped.

`verify.py report <repo>` prints this. `report --json` and `status --json` print it as one object,
with the same exit codes as `status` (0 green or no VERIFY.md, 1 red, 3 stale, partial or never
run):

```json
{"verdict": "green", "state": "green", "detail": "", "exit": 0,
 "verify_line": "VERIFY: 2 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | ...",
 "rejections": [{"feature": "Create note", "command": "...", "wrong_state": "<fail-proof>",
                 "fail_signal": "expected stored note 'Release checklist'", "exit": 1,
                 "observed": "expected stored note 'Release checklist', got ['Grocery list']"}],
 "passed": [{"feature": "Create note", "command": "..."}],
 "gaps": {"failing": [], "unverified": [], "unproven": [], "orphan_tests": [], "blind_spots": []},
 "strict": true, "rounds": 0, "failing": [], "checks": 2, "receipts": ["..."], "challenge": null}
```

`state` is the finer status (`tampered`, `out-of-scope`, `never-run`, `none`) behind the verdict.
`run --json` reports one run as it happens, and it carries `verify_line` too. Drive, RUN.json,
release gates and project `verify` skills read this answer. Pass it on unchanged. A caller may
add its own verdict next to it, but never in place of it.

## How to call verify-loop

From a skill, an agent or a prompt, say "use verify-loop" and pass:

- **claim:** the observable behavior, and where its expected result comes from;
- **scope:** a diff, base ref, commit or paths, plus adjacent callers that must stay green;
- **mode:** `assess` (report only), `prepare` (build or repair the recipe) or `repair`
  (authorized fix), with any wrong state the check must reject (table above).

You get the answer above. If you only need the current verdict and the inputs are unchanged, run
`verify.py status --json` yourself. Load the skill only when proof is missing, stale or red.
A project that has `.claude/skills/verify/` (see [create](create.md)) routes through the same
answer.

## When this skill is not installed

Look in the installed plugin's sibling skills and the available skill catalog first. If it is
truly absent, run the same check directly before and after, keep both outputs, and say that
reusable strict evidence is missing.
