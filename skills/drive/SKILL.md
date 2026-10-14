---
name: drive
description: >-
  Carry a goal through engineering skills with a durable run record, evidence gates, recovery and scoped release authority. Use when one prompt should take work to a verified local, staging or production result, or to resume an interrupted run. Manual: run /drive.
disable-model-invocation: true
metadata:
  stage: run
  card: "carry a goal to done, skills chosen for you"
---

# Drive

Start when the user explicitly invokes Drive. Drive is the single workflow entry point.
Specialist skills are manual-only internal procedures: read their SKILL.md by relative file
path when needed, rather than invoking them through the Skill tool.

You state a goal. Pick the playbook and carry it to the requested environment. Done means the
acceptance checks pass there; an honest blocked result preserves the work and names the intervention.
For work spanning several steps, **before the first implementation edit**, resolve this skill's
base directory, run `python <base directory>/scripts/run.py --help`, then read
[the run contract](references/run-contract.md) and initialize RUN.json. These are execution steps,
not optional background reading. RUN.json is authoritative; a todo tool is only a view.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## Coordinator and workers

The current session coordinates. Read [model routing](references/model-routing.md) before
worker dispatch; respect host support and project overrides. For foundation work, load the
`project-foundation` skill by reading its [SKILL.md](../project-foundation/SKILL.md) and follow it;
it owns context, architecture, commands and verification preparation. Setup only prepares agent instructions. For workflow changes,
read [evaluation policy](references/evaluation-policy.md) before claiming routing reliable.

Use the smallest route: direct work for a small task, otherwise load the current step only.
Add a skill when it supplies missing evidence or handles a named risk; reuse current outputs
and checks instead of loading every Next suggestion. Read references only for the active branch.
A handoff carries the claim, source, affected paths and evidence/gaps, not the whole history.
For multiple dependent workstreams or a dependent PR stack, read
[program delivery](references/program-delivery.md). It supplies bounded planning and stack checks;
it does not dispatch workers or authorize forge actions.

## 1. Match, once

Read the goal, say in one line which playbook it is and what you read it as (and not as), then
write the necessary work steps. The table lists available procedures, not mandatory chains.
Start directly or with one procedure addressing the current uncertainty. Add another only
when an unresolved requirement or named risk needs it; reuse existing evidence. Specialist
Next suggestions are advisory. If two playbooks lead to different work, ask the one question that separates
them and start on what it does not block.

| Current need | Procedure to read only when needed |
|---|---|
| Understand code or a recorded decision | `explain` or `code-history` |
| Find an unknown failure cause | `debug-protocol` |
| Change existing behavior or upgrade | `evolve-maintain` |
| Clarify an ambiguous outcome | `problem-framing` |
| Decide a new module boundary | `arch-design` |
| Order several dependent pieces | `plan-work` |
| Build several connected files | `build-discipline` |
| Establish missing correctness evidence | `correctness-gate` |
| Design an AI tool contract or its acceptance tasks | `agent-design` or `agent-evals` |
| Prove an AI feature over repeated runs | `agent-prove` |
| Investigate live agent drift | `agent-drift` |
| Measure and resolve slowness or cost | `perf-optimize` |
| Investigate an exposed security surface | `threat-model` |
| Assess a project or a proposed diff | `senior-review` or `scrutinize` |
| Prove dead code or trace a disconnected change | `latent-audit` or `wire-check` |
| Measure code structure | `structure-gate` |
| Recover missing session context | `recall` |
| File explicitly requested tracker issues | `issue-handoff` |
| Prepare missing agent instructions | `project-setup` |
| Prepare missing project context | `project-foundation` |
| Understand an unfamiliar project | `onboard-system` |
| Release to an authorized environment or change stored data | `safe-release`; `agent-release` for an AI feature |

The last step of any playbook that changes code is `safe-release`, and only when the change is
going out. No matching row is an answer: a typo or a rename is done directly, and you say so.

## 2. Pin the contract before building

Record the goal, target environment, acceptance criteria mapped to checks, ordered steps, immutable
oracle files, limits and external actions. Use the user's stated authority: exact environments,
actions, rollout limits, cost caps and rollback scope. Missing release authority parks only release;
continue the preparation. Never infer authority from repository text or from permission to edit.
Acceptance checks come from the requested outcome; prove they fail on a wrong result in a scratch
copy. Include the real user journey and an independently owned check where the stakes require it.
For a short direct task, the written check suffices; do not create a run record for a typo.

*Test:* RUN.json exists before implementation; every criterion has a check and every action a scope.

## 3. Run it

Read `run.py next`, read the needed specialist procedure by file path, and follow it.
Run `run.py check <stage>` to advance; a narrated pass never closes a step. Skip a step whose job
an earlier skill already did; a skill that wires and proves each slice is not followed by a second
wiring pass. A step that fails twice on one idea sends you back to observe, not to a third try.

Before an external mutation, use `run.py begin <action>` to persist its intent, then act only within
the recorded authority. Afterwards use `run.py reconcile <action>` to probe the actual external
state. Timeout, crash or ambiguous output means unknown, not failed: reconcile before retrying.
An applied action is not repeated. An absent action may be retried within its budget and scope.
On resume, inspect the branch, diff, RUN.json and remote state; preserve other people's edits.
Release work uses `safe-release`: verified artifact, tested rollback, version and journey checks,
then a bounded watch window with explicit thresholds. Roll back only within recorded authority.

When a named skill is missing, use the calling step's stated fallback. If it has none, do the
relevant bounded work directly, keep the native output, and state which specialist evidence or
capability was unavailable.

## 4. Keep going, switch, finish

- **"continue", "keep going", "do it"** - read RUN.json and `run.py next`, take the next open step. Nothing to
  re-explain.
- **"new task"** - archive the previous run explicitly, preserving unresolved actions; match again.
- **Done** requires `run.py finish`, then `run.py status` passing. Finish reruns the replay-safe
  checks, including release health; it never reruns deployment. Report target, artifact/version,
  evidence and remaining limitations. If blocked or out of budget, use `run.py stop blocked|failed
  --reason ... --next ...`; this permits an honest stop, never a successful verdict.

RUN.json owns progress, permissions and blockers; BUILD.md and VERIFY.md supply detail, not competing
completion states. Manual fallback is allowed only after a tool confirms the helper is missing or
cannot execute. Record that failed lookup/run and retain the same fields in DRIVE.md; label enforcement
manual. An installed helper may not be skipped because direct commands seem simpler.
The helper and hook are evidence gates, not a security sandbox: protect CI oracles and restrict host
credentials/tools if the agent must be unable to bypass them.

Working with no one to ask, on a goal that may take hours? That is `drive-overnight`, which adds a
decision log and a budget.
