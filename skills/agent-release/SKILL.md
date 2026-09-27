---
name: agent-release
description: Ship an AI agent with the controls it needs and keep proving it after launch: kill switch, spend and step caps, pinned model, logged runs, staged rollout, and production failures turned into new evals. Use when an agent that passed its evals is about to go live, or when a live agent needs monitoring.
---

# Agent Release

`safe-release` gives any change a way back. An agent needs four more things, because its behaviour
can shift without anyone changing the code. Run this alongside `safe-release`, after `agent-prove`
has met its bar.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Before it goes live

1. **A kill switch** that stops the agent without a deploy, and the one-line way to use it.
2. **Caps.** Steps per run, spend per run and per day, and what it does when it hits one (stop and
   report, not retry forever).
3. **Pinned versions.** Model and prompt fixed by exact identifier, so a provider update cannot
   change behaviour silently. Changing either re-runs `agent-prove`.
4. **Logged runs.** Input, every tool call, output, cost, and the version pair, so a bad run can be
   replayed. Redact secrets and personal data before they are stored.
5. **Staged rollout.** Shadow or read-only first, then a slice of traffic, with the rate you will
   compare against named beforehand. One-way actions the agent can take (sending, paying, deleting)
   stay behind a human confirm until the slice is clean. Going live is itself one-way: ask the
   person before the first live traffic and before each widening, since a yes to one stage does not
   cover the next.

*Test:* you can turn it off and roll the prompt back, and say each in one sentence.

## After it is live

6. **Sample and grade.** On a named schedule with a named owner (write both in the release note, or
   write "none" so the gap is visible), grade a sample of real runs with the same graders.
7. **Every real failure becomes a task** in the eval set, with a grader, before it is fixed. The set
   then grows with the mistakes it caught.
8. **Watch for drift:** pass rate, cost and latency per version, and a spike in refusals, retries or
   cap hits.

*Test:* the last production failure exists as a task that would have caught it.

## Common mistakes

A prompt that says "never" where a permission should be removed; no cap on spend; an unpinned model;
logs nobody can replay; rolling out to everyone at once; fixing a production failure without adding
its test.

## Next

The release itself and any stored-data change: `safe-release`. A failure to trace: `debug-protocol`.
Without those loaded, do the step plainly and say the skill was missing.
