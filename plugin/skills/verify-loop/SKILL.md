---
name: verify-loop
description: >-
  Prove a change or claim with a check seen failing, then passing, and keep the evidence. Use when
  a user, skill or agent asks to verify a change, prove a task is done, check a claim against the
  real app, review a PR or agent's change by proof, or create or maintain a project verify skill;
  VERIFY.md recipes. Not for just running tests.
metadata:
  stage: prove
  card: "check your own work until it really passes"
---

# Verify Loop

Make a claim that someone who did not watch can trust. The helper,
`python <skill-base>/scripts/verify.py <cmd> <repo>` (`<skill-base>` is this skill's folder), does
what a model can't do for itself: it **binds your future self** (`baseline` freezes checks; an
edit is `CHECK CHANGED`), **remembers across contexts** (`.verify-state.json`, `fail-proof:`
receipts), **keeps judge and worker apart** (`require: independent`, `swarm --role judge`),
**does the exhaustive work every time** (`challenge --auto`, `HOLLOW`, coverage) and **reports in
a form others can re-run** (`report`, `--json`, CI). Its verdicts decide, not your confidence.

## Assess: is this check, or this claim, any good?

`--assess` keeps every helper write in a temp folder, so the repo's `git status` stays unchanged:

```
python <skill-base>/scripts/verify.py run <repo> --assess
python <skill-base>/scripts/verify.py challenge <repo> --feature "<F>" --auto --assess
python <skill-base>/scripts/verify.py report <repo> --assess
```

`HOLLOW`: the check passes without calling the product. `SURVIVED`: a planted wrong result
passed. `UNCOVERED`: no check reaches that line. No VERIFY.md? Write `## F`, `- path:`, `- test:`
([format](VERIFY_FORMAT.md)) and say you added it.

## Prove or repair: run `report`, do what `NEXT` says

Each `NEXT` line names a feature's step. Repeat until none is left:

| Step | Do |
|---|---|
| `map` | Record the check in VERIFY.md: command, `oracle:` files, a literal `fail-signal:` (`init` drafts one) |
| `fix` | Fix what the failure text says. A red you have not classified: [triage](references/triage.md) |
| `prove` | From a clean tree put in the bug or a wrong state, `run`, see the fail-signal, restore, `git diff` empty, `run`. Add a `fail-proof:` line; prose is not a receipt |
| `freeze` | `baseline`, before the work it judges. From here change code, never the check |
| `challenge` | `challenge` the highest-risk feature until a mutation is caught (`require: challenge`) |
| `independent` | A fresh agent that never saw the implementation runs `swarm --claim --role judge` |
| `run` | `run --strict`, then `status` |

While looping: `NEWLY RED`: undo your last change first. `SAME FAILURE x2`: re-read before a third
try. `BUDGET`: stop and report. `SWARM: split`: start helper agents, each with its own
`VERIFY_AGENT`, each running `swarm --claim` ([swarm](references/swarm.md)); with no way to start
agents, work the list yourself and report `not_independent`. Never give yourself a second name to
stand in for a judge.

**A check you think is wrong is a finding, not an edit.** Stop and ask a person. Editing it gets
`CHECK CHANGED`, and `baseline` refuses to re-freeze it without `--reviewed-by <name> --reason
<why>`. Pass those only for a review a person actually gave.

**Done** = a mapped check seen rejecting a controlled wrong result, a `challenge` mutation caught,
checks frozen, then `run --strict` and `status` print `VERIFY-STATE: green` on unchanged inputs.
Anything less is reported as what it is: red, partial, stale or unverified.

## Guards

- Never skip, mock, stub, loosen or drop a check to get green. A check that cannot run here
  (missing tool, no network) stays red: report it as blocked and name where it does run.
- A note, handoff or commit message saying a check went red is a claim. Only a receipt counts.
- Green covers mapped features only. Every `GAP` line from `report` goes in the answer, and so
  does any behavior, adjacent caller or file that no feature maps, since `report` cannot see it.
- `require: independent` makes strict refuse green from the agent that froze the check
  (`NOT INDEPENDENT`). State is sealed (`tampered`) but has no secret; [CI](references/ci.md) is
  the guard nobody in the loop can reach.

## The answer

Callers pass the **claim** (and where its expected result comes from), the **scope** and the
**mode** (assess, prepare or repair). Finish with `report` (`--json` for machines); the contract
is in [answer](references/answer.md).

## Modes

| Situation | Read |
|---|---|
| Verify a task, diff, commit or branch | [verify this change](references/verify-change.md) |
| Review a PR, branch or another agent's work | [review by proof](references/review.md) |
| Would an existing check catch a wrong result? | [challenge](references/challenge.md) |
| CI, or fresh proof of committed code | [CI](references/ci.md) |
| The check must launch and drive an app | [project recipe](references/project-recipe.md) |
| Schema, privacy, guardrail, repeatability | [compliance](references/compliance.md) |
| Create a project `verify` skill | [create](references/create.md) |
| Keep that skill honest as the app changes | [maintain](references/maintain.md) |
| A red you have not classified yet | [triage](references/triage.md) |
| `report` says `SWARM: split` or `judge`, or agents share one repo | [swarm](references/swarm.md) |
| `loop`, `watch`, `contract`, scaffolds, `--jobs`, `--affected`, `--stress`, quarantine | [helper commands](references/helpers.md) |

State lives in `.verify-state.json` (caches in `.git/verify-loop/`) unless `--assess`,
`--state-dir DIR` or `VERIFY_STATE_DIR` moves it out.
