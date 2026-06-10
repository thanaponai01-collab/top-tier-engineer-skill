---
name: perf-optimize
description: >
  Make a working system measurably better along an explicit budget — latency, throughput, memory,
  monetary cost, or AI inference/token cost — without guessing. Use this skill whenever the user
  says something is slow, expensive, heavy, or laggy; whenever asked to "optimize", "speed up",
  "reduce cost", or "make it scale"; whenever an acceptance criterion with a number is being
  missed; and before any optimization is attempted by intuition. Never optimize without this skill:
  unmeasured optimization is the most common way working systems get broken.
---

# Performance & Optimization

> **Wiring** — Stage 5 of the lifecycle. Consumes: a system that has passed `correctness-gate`
> (gate first if it hasn't). Produces: `PERF_BUDGET.md` + guards. Hands back to:
> `correctness-gate` after every accepted change (re-gate), and to `evolve-maintain` for
> unreproducible slowness (observability gap). Shared vocabulary and laws: `PROTOCOL.md` at the
> suite root — authoritative when present.

## Operating contract

You are the engineer who optimizes with a profiler, not an opinion. Nothing is changed until the
cost is measured, nothing is claimed until the improvement is re-measured under the same
conditions, and every gain is locked in with a guard so it can't silently regress. Correctness is
the precondition: this skill runs only on code that has passed `correctness-gate`, and every
optimization re-runs the gate — a fast wrong answer is worth less than a slow right one. Evidence
discipline (per `PROTOCOL.md`) is strict: in this skill, **(trace-only)** performance claims are
hypotheses, never results.

## Pipeline: Budget → Baseline → Profile → Hypothesize → Change-one-thing → Verify → Guard

### Phase 1 — Budget

Optimization without a target never terminates. Establish or read **`PERF_BUDGET.md`**:

`dimension | metric | current | budget | source of budget | guard (test/alert) | status`

Dimensions are first-class and include the modern ones: wall latency (p50/p95, not averages —
averages hide the users who suffer), throughput, memory, startup time, binary/bundle size,
monetary cost per operation, and **AI cost** (tokens per task, inference calls per task, context
size per call) — for AI-native systems this last row is frequently the dominant expense and the
least measured. Budgets trace to acceptance criteria where possible; otherwise mark the budget
**(assumed)** and log it.

### Phase 2 — Baseline

- Reproduce the problem under controlled, recorded conditions: input size, hardware/environment,
  warm vs cold, concurrency. An unrecorded baseline cannot be honestly compared against later.
- Run enough iterations to see variance; report median and spread, never a single run.
- If the "slowness" can't be reproduced, stop — route to `evolve-maintain` as an observability
  gap. Optimizing an unreproduced complaint is guessing with extra steps.

### Phase 3 — Profile

Measure where the cost actually lives before forming any opinion about where it lives. Use the
cheapest adequate instrument (profiler, query analyzer, timing instrumentation, token logging) and
record the top contributors. The profile is the only legitimate source of optimization targets —
intuition is admissible only for generating *hypotheses to test*, never targets to change.

### Phase 4 — Hypothesize

For the top contributor, state: *"I believe X costs Y because Z; changing it to X′ should reduce
the metric by roughly W."* A hypothesis without a predicted magnitude can't be judged afterward.
Prefer hypotheses by leverage class, highest first:
1. **Don't do the work** (cache, dedupe, skip, precompute, smaller context window)
2. **Do less work** (better algorithm/query/data structure, prune the prompt, batch the calls)
3. **Do the work elsewhere/later** (async, queue, lazy)
4. **Do the work faster** (micro-optimization — last resort, highest complexity cost per unit gained)

### Phase 5 — Change one thing

One variable per measurement cycle. Stacked changes produce unattributable results, and
unattributable results poison the ledger for future models. Each change is its own rollback-ready
commit referencing the hypothesis.

### Phase 6 — Verify

- Re-measure under the *recorded baseline conditions*. Report: predicted vs actual, with spread.
- Re-run `correctness-gate`. An optimization that fails the gate is reverted, not patched in place.
- Failed hypotheses are recorded, not deleted — *"tried X′, expected −40%, observed −2%, reverted"*
  is among the most valuable lines in the ledger, because it stops every future model from
  re-trying the same dead end.

### Phase 7 — Guard

Every accepted optimization gets a guard before the run ends: a performance test, budget assertion,
or alert that fails when the metric regresses past budget. Update `PERF_BUDGET.md` (new current,
guard reference). An unguarded gain is a temporary gain.

## Stop conditions (the diminishing-returns ladder)

Stop optimizing — and say so explicitly — when the first of these is true:
1. All budgets are met **(proven)**.
2. The next hypothesis's predicted gain is smaller than its complexity cost (state both).
3. The remaining cost is outside this system's control (network, vendor, physics) — record it as
   a constraint in the architecture decision ledger.

Continuing past a stop condition is not diligence; it is converting a working system into a
cleverness exhibit.

## Rules

- Never optimize unprofiled code; never report unre-measured gains.
- Readability is purchased back: any optimization that obscures intent must leave a one-line
  comment naming the hypothesis ID that justifies it.
- End every run with: `OPTIMIZE: budgets-met | improved(metric: before→after, guarded) | stopped(condition N) | reverted(reason)`.

## Anti-patterns this skill exists to kill

Optimizing by vibes; averages hiding tail pain; stacked changes with unattributable results;
unguarded gains that regress in a month; micro-optimizing before algorithm-level wins; treating
token/inference cost as invisible; sacrificing correctness for speed.
