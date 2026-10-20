---
name: verify-loop
description: >-
  Prove a change or claim with a check seen failing, then passing, and keep the evidence. Use when
  a user, skill or agent asks to verify a change, prove a task is done, check a claim against the
  real app, or create or maintain a project verify skill; VERIFY.md recipes. Not for just running tests.
metadata:
  stage: prove
  card: "check your own work until it really passes"
---

# Verify Loop

Build the check before the work, make it hard to fool, loop until it passes.

The point is not that you are sure; it is that someone who did not watch can trust the claim.

**Done** = one mapped check seen rejecting a controlled wrong result, the highest-risk check seen
catching a `challenge` mutation, checks frozen with `baseline`, then `run --strict` and `status`
print `VERIFY-STATE: green` on unchanged inputs. `verify.py` decides these, not your confidence.
Anything less is reported as what it is: red, partial, stale or unverified.

## A good check

1. **Can fail.** You watched it go red on a wrong result, for the declared `fail-signal:`, not a
   crash or timeout. Then restored and watched it pass.
2. **Watches the real thing.** Runs the program, hits the endpoint, drives the UI. Not a mock of
   the code under test.
3. **Expects what the spec says.** Expectations come from the task, spec or contract, never from
   the implementation's own output.
4. **Fails specifically.** Names expected versus actual.
5. **Is one cheap command.**

A check that loads no cases, asserts nothing or passes either way is broken machinery, not
evidence.

## The loop

`<skill-base>` is this skill's directory; the helper is `python <skill-base>/scripts/verify.py`
(pass the project as its repo argument; `--help` lists everything).

1. **Name the claim** observably. Not "refunds work" but "POST /refund on a paid order returns 200
   and the balance drops by the amount".
2. **Pick the strongest check you can run**: lint < unit < integration < real run < real data,
   and above that property-based, differential, metamorphic or formal checks. There is no top
   rung: take the strongest this environment affords, plus one below for a fast signal.
3. **Record it** in VERIFY.md ([format](VERIFY_FORMAT.md)): command, `oracle:` files, literal
   `fail-signal:`. Reuse the project's harness; `init` drafts from existing tests.
4. **Prove it fails.** From a clean tree, put in the original bug or a deliberate wrong state,
   `run`, see the fail-signal, restore, confirm `git diff` is empty, `run` again. Add a
   `fail-proof:` line. Prose is not a receipt. Then `challenge` the highest-risk feature; keep
   `require: challenge` in VERIFY.md so strict stays red (`UNCHALLENGED`) until one is caught.
5. **Freeze**: `baseline`. From here change code, never the check.
6. **Slice and run.** Fix what the failure text says. `NEWLY RED`: undo your last change first.
   `SAME FAILURE x2`: your model is wrong; re-read before a third try. `BUDGET`: stop and report.
7. **A check you think is wrong is a finding, not an edit.** Stop for a person. Editing it
   yourself gets `CHECK CHANGED`, and `baseline` refuses to re-freeze a changed or removed check
   without `--reviewed-by <name> --reason <why>`. Pass those only for a review a person actually
   gave; the re-baseline is recorded and shown in `status` and `report`. New checks need no review.
8. **Finish**: `run --strict && status` → green. If you touched tests, `tests --strict`.

## Before you say done

Green only covers what is mapped. Look for what it cannot show and report it:

- a changed behavior or adjacent caller with no check
- a check never seen red
- a deleted, skipped or loosened test; an output hardcoded to match
- a stale process or build answering instead of the code you changed
  ([artifact identity](VERIFY_FORMAT.md#run))

An assessment reports; it edits product code only when a fix was asked for.

## Assume the checker can be fooled, by you too

A capable agent can pass a weak check without doing the work: hardcode the output, mock the thing
under test, loosen an assertion, narrow the claim. The stronger the agent, the more this matters.
Guard structurally, not with good intentions:

- **Separate judge from worker.** Where you can, have a fresh context (a subagent, a reviewer, CI)
  write or challenge the check without seeing the implementation. `require: independent` makes
  strict enforce it: the `VERIFY_AGENT` that ran `baseline` on a check cannot be the one whose run
  claims green (`NOT INDEPENDENT`). Names are not credentials; give each context its own honestly.
- **Freeze before you build.** `baseline` comes before the work it judges, and re-freezing a
  weakened check needs a named reviewer (step 7).
- **Prefer evidence a third party can re-run.** `.verify-state.json` is sealed, so a hand edit
  shows as `tampered`, but the seal has no secret. Independently owned [CI](references/ci.md) is
  what nobody in the loop can reach.

## The answer

Callers pass the **claim** (and where its expected result comes from), the **scope** and the
**mode** (assess, prepare or repair). Finish with `verify.py report` (`--json` for machines); the
contract is in [answer](references/answer.md).

## Modes

| Situation | Read |
|---|---|
| Verify a task, diff, commit or branch | [verify this change](references/verify-change.md) |
| Would an existing check catch a wrong result? | [challenge](references/challenge.md) |
| CI, or fresh proof of committed code | [CI](references/ci.md) |
| The check must launch and drive an app | [project recipe](references/project-recipe.md) |
| Schema, privacy, guardrail, repeatability | [compliance](references/compliance.md) |
| Create a project `verify` skill | [create](references/create.md) |
| Keep that skill honest as the app changes | [maintain](references/maintain.md) |
| A red you have not classified yet | [triage](references/triage.md) |
| `loop`, `watch`, `contract`, scaffolds, quarantine | [helper commands](references/helpers.md) |

## Other helper commands

`run --affected [--record-coverage] | --jobs N | --stress N | --quarantine | --json | --no-cache` (checks get
`VERIFY_SLOT`/`VERIFY_PORT`; a pass already proved on identical content is reused, never a
non-strict one for `--strict`) · `triage` · `scope <files>` (fence a fix;
`OUT OF SCOPE` / `KEEP-GREEN BROKEN`) · `challenge . --feature F --auto [<file>] [--diff [REF]] [--jobs N]` (mutation score, `--diff` = only changed lines; `UNCOVERED` = no check reaches the line) ·
`loop --scope <f> --max N` (reruns, never edits) ·
`VERIFY_AGENT=<name>` (own loop memory per agent, shared baseline) ·
`watch --max-runs N` (never exits without it) · `contract old new` · `scaffold-oracle | scaffold-ui |
scaffold-driver` · `scaffold-skill` · `skill-check` · `maintain` · `ci`. What each does and
when it is safe: [helper commands](references/helpers.md). Evidence lives in
`.verify-evidence/` and `.verify-state.json`.

*Test:* the check existed before the change it judges, you can name the moment it was red, and
`status` is green on the final inputs.
