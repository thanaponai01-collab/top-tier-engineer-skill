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

Make a claim that someone who did not watch can trust. `H` below is
`python <skill-base>/scripts/verify.py` (`<skill-base>` is this skill's folder). The helper does
what a model can't do for itself: it binds your future self (frozen checks), remembers across
contexts (receipts), keeps judge and worker apart, does the exhaustive work every time (mutation
surveys, `HOLLOW`) and drafts the answer. Its verdicts decide, not your confidence.

## One command per question

| Question | Run |
|---|---|
| Is this check, claim or change any good? Report only | `H assess <repo>` |
| Make it proven, repair it, keep it proven | `H advance <repo>`, again after each task, until `ADVANCE: done` |
| Has anything changed since the last green? | `H status <repo>` |

`assess` runs every check, plants wrong results in each passing feature's product code and
reports, with its state in a temp folder: the repo is left as it was. No VERIFY.md? It prints the
lines to write; say in the answer that you added them.

**Read the output, not the scripts.** Every verdict line says what it found and what to do. Do
that, then run the same command again. A refusal lists every problem at once, each with its fix,
so the helper's source never needs reading. Flags and rare commands: [helpers](references/helpers.md).

## Tasks `advance` returns (and `NEXT` in `report`)

| Task | Do |
|---|---|
| `repair` | The check is `HOLLOW` and not frozen: edit it until it calls the product. No review needed |
| `map` | Add the check to VERIFY.md: command, `oracle:` files, a `fail-signal:` naming the wrong result |
| `blocked` | The environment failed (tool, port, timeout). Report it blocked and where it runs; change no code |
| `fix` | Fix what the failure text says. A red you can't classify: [triage](references/triage.md) |
| `prove` | Put the wrong result in the product (inside `path:`), run, see the fail-signal, restore, run. Add a `fail-proof:` line |
| `challenge` | `challenge` the highest-risk feature until a mutation is caught |
| `independent` | A fresh agent that never saw the implementation runs `swarm --claim --role judge` |

`NEWLY RED`: undo your last change first. `SAME FAILURE x2`: re-read before a third try. `BUDGET`:
resume with `advance` or report. `SWARM: split`: start helper agents, each with its own
`VERIFY_AGENT` ([swarm](references/swarm.md)); with no way to start one, work the list yourself and
report `not_independent`. Never give yourself a second name to stand in for a judge.

**A check you think is wrong is a finding, not an edit**, unless the task is `repair`. Stop and ask
a person. An edit gets `CHECK CHANGED` (or `LOOSENED` before a baseline), and `baseline` refuses
it without `--reviewed-by <name> --reason <why>`. Pass those only for a review a person gave.

## Done, and the answer

**Done** = a mapped check seen rejecting a wrong product, a `challenge` mutation caught, checks
frozen, no `UNMAPPED` or `LOOSENED`, and `advance` stops `done` on unchanged inputs. Anything less
is reported as what it is: red, partial, stale or unverified.

`assess`, `advance` and `report` end with an `ANSWER DRAFT`. Copy it to a file outside the repo,
replace each `[[fill: ...]]` with your judgment (the claim and its source, what each gap means,
each survivor: real gap or equivalent mutation), keep every other line and run its `Then:` line.
`answer-check` refuses an answer that is `UNFILLED`, has `NO VERDICT`, has an `OVERCLAIM` or is
`MISSING` a gap, and prints the line that fixes each. Send only an answer it accepts.

## Guards

- Never skip, mock, stub, loosen or drop a check to get green. A check that cannot run here stays
  red: report it blocked and name where it does run.
- A note, handoff or commit message saying a check went red is a claim. Only a receipt counts.
- Green covers mapped features only. Behavior inside a mapped file that no check exercises still
  needs your eyes; `assess` survivors point at it.
- `require: independent` refuses green from the agent that froze the check (`NOT INDEPENDENT`).
  [CI](references/ci.md) is the guard nobody in the loop can reach.

## Modes

| Situation | Read |
|---|---|
| Verify a task, diff, commit or branch | [verify this change](references/verify-change.md) |
| Review a PR, branch or another agent's work | [review by proof](references/review.md) |
| Would an existing check catch a wrong result? | [challenge](references/challenge.md) |
| CI, or fresh proof of committed code | [CI](references/ci.md) |
| The check must launch and drive an app | [project recipe](references/project-recipe.md) |
| Schema, privacy, guardrail, repeatability | [compliance](references/compliance.md) |
| Create, or keep honest, a project `verify` skill | [create](references/create.md), [maintain](references/maintain.md) |
| What callers pass and get back; JSON | [answer](references/answer.md), [format](VERIFY_FORMAT.md) |
