---
name: agent-release
description: 'Ship an AI agent with the controls it needs and keep proving it after launch: kill switch, spend and step caps, pinned model, logged runs, staged rollout, and production failures turned into new evals. Use when an agent that passed its evals is about to go live, or when a live agent needs monitoring.'
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
   require the user's scoped grant until the slice is clean. First live traffic and widening must
   fit recorded environment, traffic and spend limits; an upfront grant may cover those stages and
   rollback. Ask when widening exceeds it. Configure tool permissions and provider caps outside
   the agent's writable files; a recorded grant alone cannot enforce access.

*Test:* you can turn it off and roll the prompt back, and say each in one sentence.

Reusable proof: when VERIFY.md exists or reusable release-control verification is requested, hand
checks for the real kill switch, step/spend caps and log redaction to `verify-loop`: load that
skill, follow its references/handoff.md and record the rejection and strict green through its
bundled `verify.py`. Direct output files are the fallback only when verify-loop is not installed.
Exercise cap hits and shutdown with fake tools and bounded workloads; the wrong state is a broken
control in scratch. Agent-prove still owns repeated behavioral evaluation; safe-release owns
deployment and rollback.

## After it is live

6. **Sample and grade.** On a named schedule with a named owner (write both in the release note, or
   write "none" so the gap is visible), grade a sample of real runs with the same graders.
7. **Every real failure becomes a task** in the eval set, with a grader, before it is fixed. The set
   then grows with the mistakes it caught.
8. **Watch for drift**, on the same named schedule and owner as step 6 — a metric nobody is due to
   look at is not being watched: pass rate, cost and latency per version, and a spike in refusals,
   retries or cap hits. Name the threshold that pages someone, not just the metric. `agent-drift` is
   the full mechanics for 6–8 — the noise band, the sampling size, and the root-cause order — run it
   on the named schedule rather than re-deriving these three lines each time.

*Test:* the last production failure exists as a task that would have caught it.

## Common mistakes

A prompt that says "never" where a permission should be removed; no cap on spend; an unpinned model;
logs nobody can replay; rolling out to everyone at once; fixing a production failure without adding
its test.

## Next

The release itself and any stored-data change: `safe-release`. The ongoing drift check once it's
live: `agent-drift`. A failure to trace: `debug-protocol`. Without those loaded, do the step plainly
and say the skill was missing.
