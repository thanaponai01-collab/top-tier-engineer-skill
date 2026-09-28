---
name: drive
description: Give it a goal and it matches a playbook, writes the steps into the todo list, and carries the work through the other skills to a passing check. Use as the one entry point when you know what you want done but not which skills it takes: "/drive users get two notifications after a retry, repro first then fix", or just "continue" or "new task" mid-run.
---

# Drive

You state a goal. This skill picks the playbook, turns it into a todo list, and runs it. Each step
calls the skill whose job it is; you never list the skills yourself.

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
| New behavior | `problem-framing` (only if "done" is unclear) → `arch-design` (only if it needs a new boundary) → `build-discipline` → `correctness-gate` |
| An AI agent or model-driven feature | `problem-framing` (only if "done" is unclear) → `arch-design` (only if it needs a new boundary) → `agent-evals` (before any agent code) → `build-discipline` → `agent-prove` (includes the `threat-model` abuse cases) → `safe-release` + `agent-release` when it goes out → `agent-drift` on the schedule once it's live |
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

## 2. Write the todo list

One line per step, each with the check that means that step is done (a repro that now passes, the
same tests green before and after). Put the exit check for the whole goal on the first line, before
any step runs, with a budget beside it (the number of steps you expect, and a stop at about double).
Hit the budget: stop and report what passed, what failed and what you would try next. If the agent has no todo tool, keep the list in a file called `DRIVE.md` at the
repo root, so it survives the context.

*Test:* the list was written before the first step ran, and every line names its check.

## 3. Run it

Take the first open step and invoke its skill with the Skill tool (load it, follow it; do not do that
skill's work from memory), then tick it only when its check passed. Skip a step whose job
an earlier skill already did; a skill that wires and proves each slice is not followed by a second
wiring pass. A step that fails twice on one idea sends you back to observe, not to a third try.

A one-way action (a deploy, deleted data, a message sent, a public API changed) stops the run and
asks. A yes covers that action only.

Where a named skill is not installed, do that step plainly and say the skill was missing.

## 4. Keep going, switch, finish

- **"continue", "keep going", "do it"** — read the todo list, take the next open step. Nothing to
  re-explain.
- **"new task"** — drop the list and match again. Say what was left open, so it is not lost.
- **Done** is the exit check passing, reported first: the verdict, then what you ran
  ([proven]), then what you did not check. If you stopped short, say where and why.

Working with no one to ask, on a goal that may take hours? That is `drive-overnight`, which adds a
decision log and a budget.
