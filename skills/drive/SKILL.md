---
name: drive
description: >-
  Carry a goal through engineering skills with a durable run record, evidence gates, recovery and scoped release authority. Use when one prompt should take work to a verified local, staging or production result, or to resume an interrupted run. Manual: run /drive.
disable-model-invocation: true
---

# Drive

You state a goal. Pick the playbook and carry it to the requested environment. Done means the
acceptance checks pass there; an honest blocked result preserves the work and names the intervention.
For work spanning several steps, **before the first implementation edit**, resolve this skill's
base directory, run `python <base directory>/scripts/run.py --help`, then read
[the run contract](references/run-contract.md) and initialize RUN.json. These are execution steps,
not optional background reading. RUN.json is authoritative; a todo tool is only a view.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 1. Match, once

Read the goal, say in one line which playbook it is and what you read it as (and not as), then
write the steps. If two playbooks lead to different work, ask the one question that separates
them and start on what it does not block.

| The goal | Steps |
|---|---|
| A question about the code | `explain` or `code-history`. Read-only; nothing else runs. |
| Broken, cause unknown | `debug-protocol` → fix with `evolve-maintain` → `correctness-gate` |
| Broken, cause known; refactor; upgrade | `evolve-maintain` → `correctness-gate` |
| New behavior | `problem-framing` (only if "done" is unclear) → `arch-design` (only if it needs a new boundary) → `plan-work` (only if it has more than one piece) → `build-discipline` → `correctness-gate` |
| An AI agent or model-driven feature | `problem-framing` (only if "done" is unclear) → `arch-design` (only if it needs a new boundary) → `agent-evals` (before any agent code) → `plan-work` (only if it has more than one piece) → `build-discipline` → `agent-prove` (includes the `threat-model` abuse cases) → `safe-release` + `agent-release` when it goes out → `agent-drift` on the schedule once it's live |
| An agent is flaky, or a model or prompt changed | `agent-prove` → fix with `build-discipline` → `agent-prove` |
| A live agent might have drifted, or a check-in is due | `agent-drift` → `agent-prove` + fix if it's real |
| Slow or expensive | `perf-optimize` → `correctness-gate` |
| Insecure, or takes untrusted input | `threat-model` → `evolve-maintain` → `correctness-gate` |
| "Is this good / should this land" | `senior-review` for a project, `scrutinize` for one diff |
| Dead code, or "is this hooked up?" | `latent-audit` for a sweep, `wire-check` for one change. Read-only until you say to delete. |
| "Is it a mess?", restructure, module boundaries | `structure-gate` to measure, `arch-design` to decide, `evolve-maintain` → `correctness-gate` per move |
| Resume, or "where were we?" | `recall`, then match the goal it surfaces |
| Plans to file as tickets | `issue-handoff` (it writes to the tracker: ask first unless the goal itself said to file) |
| A new repo, or "set this up for the skills" | `project-setup` |
| An unfamiliar codebase, or "get me up to speed" | `onboard-system` (it runs `project-setup` itself) |
| Deploy, or change stored data | `safe-release` |
| Big, vague, or matches nothing | `problem-framing` to make the goal checkable, then match again |

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

Read `run.py next`, load the named skill (with a Skill tool or by reading its file), and follow it.
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

Where a named skill is not installed, do that step plainly and say the skill was missing.

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
