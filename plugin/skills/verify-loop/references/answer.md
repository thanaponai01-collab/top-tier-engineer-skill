# Calling verify-loop, and its answer

Every caller comes in the same way and gets the same answer: a person, a skill, an agent or
another AI.

## What the caller passes

- **claim:** the observable behavior, and where its expected result comes from (spec, policy,
  contract or budget, never the code);
- **scope:** a diff, base ref, commit or paths, plus adjacent callers that must stay green;
- **mode:** `assess` (report only; a red is a valid verdict, not permission to fix), `prepare`
  (build or repair the recipe) or `repair` (authorized fix);
- **the wrong state the check must reject**, when the caller knows it: the proven cause
  reintroduced, a mutated boundary, the abuse request, the slow path, the removed connection.
  It becomes the `prove` rejection or a `verify.py challenge` mutation in a scratch copy.

If the inputs are unchanged and only the current verdict is needed, `verify.py status --json` is
enough. Load the skill only when proof is missing, stale or red.

## Rules for every caller

- Run the helper from the installed skill, never an assumed path in the target repo.
- The rejection must be the behavioral `fail-signal:`. A missing dependency, startup failure or
  timeout proves nothing.
- Mutations run in scratch copies with fake accounts and data. Never break a live system.
- Record what the result depends on (environment, target identity, workload) in the evidence.
  Keep secrets out of it.
- Repaired checks need fresh rejection evidence. Never change an expected result to match a fix.

The caller keeps its own verdict (severity, performance baseline, go/no-go) next to this answer,
never in place of it. A green recipe covers the mapped claims only.

## What comes back

The verdict first:

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
4. **Gaps:** failing checks, checks blocked by the environment, features with no check, features
   never seen red, weak fail-signals, receipts whose red did not come from the product, loosened
   tests, unmapped product files, orphan tests and blind spots.
5. **What is left and who does it:** a `NEXT` line per unfinished feature (its step and command),
   and a `SWARM:` line, `solo`, `split`, `judge` or `done` (see [swarm](swarm.md#when-the-helper-decides)).

`verify.py report <repo>` prints this, then an `ANSWER DRAFT` built from it: the verdict, each
rejection and pass, every `GAP` line, and `[[fill: ...]]` slots for what needs judgment (the claim
and its source, what is left, how each survivor reads). An answer written for a person goes through
`verify.py answer-check <repo> --answer <file>` (or `-` for stdin) first. It exits 1 with
`ANSWER NO VERDICT` when the text lacks `VERDICT: <verdict>`, `ANSWER UNFILLED` when a
`[[fill: ...]]` slot is left, `ANSWER OVERCLAIM` when a non-green answer says "ready to merge",
"all checks pass", "fully verified" or the like without a negation just before it, and
`ANSWER MISSING` for each gap item it does not name (feature names, file names, or most words of a
blind spot). It lists every problem in one pass and ends with `ADD THESE LINES`: the exact lines
that clear the verdict and missing-gap problems. `--json` gives each problem a `fix`. Keep the answer file outside the repo: writing inside it
makes the tree stale. `report --json` and `status --json` print it as one object,
with the same exit codes as `status` (0 green or no VERIFY.md, 1 red, 3 stale, partial or never
run):

```json
{"verdict": "green", "state": "green", "detail": "", "exit": 0,
 "verify_line": "VERIFY: 2 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | ...",
 "rejections": [{"feature": "Create note", "command": "...", "wrong_state": "<fail-proof>",
                 "fail_signal": "expected stored note 'Release checklist'", "exit": 1,
                 "observed": "expected stored note 'Release checklist', got ['Grocery list']"}],
 "passed": [{"feature": "Create note", "command": "..."}],
 "gaps": {"failing": [], "unverified": [], "unproven": [], "orphan_tests": [], "unchallenged": [],
          "not_independent": [], "blocked": [], "unmapped": [], "weak_signal": [], "survived": [],
          "proof_not_from_product": [], "loosened": [], "blind_spots": [], "rebaselined": []},
 "rebaselines": [],
 "next": [], "swarm": {"mode": "done", "why": "...", "judge": [], "open": []},
 "strict": true, "rounds": 0, "failing": [], "checks": 2, "receipts": ["..."], "challenge": null}
```

`gaps.survived` lists mutations an
`assess` survey planted that every check still passed, while the tree is unchanged since.
`state` is the finer status (`tampered`, `out-of-scope`, `never-run`, `none`) behind the verdict.
`unchallenged` is non-empty when VERIFY.md has `require: challenge` and no `challenge` mutation was
caught for the current checks. `not_independent` is non-empty when VERIFY.md has
`require: independent` and a check was frozen by the agent reporting (or by an unnamed one).
`gaps.rebaselined` lists frozen checks a person approved changing since the last commit, with who
and why; `rebaselines` keeps every recorded one. A caller should read these as changes to the proof.
`run --json` reports one run as it happens and carries `verify_line` too. A project
`.claude/skills/verify/` (see [create](create.md)) returns the same answer. Pass it on unchanged.

## When this skill is not installed

Run the same check directly before and after, keep both outputs, and say that reusable strict
evidence is missing.
