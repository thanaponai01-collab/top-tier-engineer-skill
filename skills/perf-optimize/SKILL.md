---
name: perf-optimize
description: >
  Make a system measurably faster or cheaper, or trace a felt complaint ("navigation takes 3 seconds", "the app feels clunky", "this report takes forever") to its real cause. Also judges whether a query will scale. Use for slow/laggy, "optimize", "speed up", "reduce cost", "make it scale", "is this an N+1 / should I add an index". Never optimize by intuition.
---

# Performance & Optimization

Optimize with a profiler, not an opinion. Nothing changes until the cost is measured, nothing is
claimed until it's measured again under the same conditions, and every gain gets a guard so it
can't slip back. Correctness first: a fast wrong answer is worth less than a slow right one. A
performance claim you only reasoned about is a hypothesis, not a result.

Pick the mode that fits:
- **Measure mode:** the system runs here and there's a number to improve.
- **Trace mode:** a felt complaint, or the system can't be run or profiled here.
- **Query-scaling mode:** a data-access change with no budget yet ("N+1?", "add an index?").

## Measure mode

### 1. Budget
Without a target, optimization never ends. `dimension | metric | current | budget | guard`.
Dimensions: user-felt time (p50/p95, never averages), throughput, memory, startup, bundle size, money
per operation, and **AI cost** (tokens, model calls, context size per task), often the biggest and
least measured. No stated budget → propose one and mark it assumed.

### 2. Baseline
Reproduce under recorded conditions: input size, hardware, warm vs cold, concurrency. Multiple
runs; report median and spread. Can't reproduce the slowness → stop and say what visibility is
missing.

### 3. Profile
Measure where the cost is before forming an opinion (profiler, query analyzer, timers, token logs).
The profile is the only source of targets. A hunch may suggest a hypothesis, never a change.

### 4. Hypothesize
*"X costs Y because Z; changing to X′ should cut it by about W."* No predicted size means it can't
be judged. Try in this order:
1. **Don't do the work** (cache, skip, dedupe, precompute, send less context)
2. **Do less work** (better algorithm, query or data structure; shorter prompt; batch calls)
3. **Do it elsewhere or later** (async, queue, lazy load)
4. **Do it faster** (micro-optimization, last resort)

### 5. Change one thing
One change per measurement, each its own revertable commit.

### 6. Verify
Re-measure under baseline conditions: predicted vs actual, with spread. Re-run the tests; an
optimization that breaks correctness is reverted. **Record failed hypotheses** ("tried X′, expected
−40%, got −2%, reverted") so nobody repeats them.

### 7. Guard
Every kept gain gets a perf test, budget assertion or alert that fails when it slips back.

### When to stop
Say so explicitly when: all budgets are met (measured); the next gain is smaller than its complexity
cost (state both); or the remaining cost is outside this system's control (network, vendor).

## Trace mode

1. **Pin the symptom.** One sentence: the operation, what it costs the user, when. "2–3 seconds
   before the next page" is *navigation*, not saving. That sentence scopes everything. Can't pin it?
   Ask one narrowing question, or take the most-used flow and say so.
2. **Map.** Read the manifest and find where this framework starts handling a request. List the
   likely path; don't read deeply yet.
3. **Trace the path in execution order**, not folder order. For each step: network call? sequential
   or parallel? cached or recomputed?
4. **Sweep the traced path only** for: work that could be skipped, reduced, deferred or sped up
   (the order above); **feel** (is anything hiding progress from the user?); **growth** (a query or
   payload that grows without limit: fine in week 1, dead in month 3). For "hangs together" complaints:
   duplicated components, state lost on navigation, dead-end flows.
5. **Diagnose.** `cause | file:line | what the user feels | proven or traced`. Several symptoms with
   one cause collapse to one row. A check that came back clean is a finding too: it says where not
   to spend effort.
6. **Prescribe in phases**, ordered by felt impact per effort. Each phase: contained code changes in
   the project's conventions, the causes it removes, an explicit out-of-scope line, what the user
   should feel after, and a before/after check someone can run. A cause that needs a rewrite is
   raised as its own decision, never buried in a phase.

## Query-scaling mode

A query fast on a thousand rows can take the system down at a million. You see it in the plan, not
on a stopwatch.

1. **List** every query, ORM call, join and index the change adds, plus any loop that could run one
   query per item. Note which tables grow with use.
2. **Classify cost growth:** flat (indexed single-row lookup), grows with result (index range scan),
   grows with table (full scan), unbounded (query per item, or a join with no selective index).
   Growing-with-table or unbounded on a growing table is a finding **even if fast today**. A query
   in a loop is one-per-item until proven otherwise; say whether the fix is a join, batch fetch or
   up-front load.
3. **Read the plan, don't time it.** Get it from the database (`EXPLAIN` / `EXPLAIN ANALYZE` or the
   engine's equivalent; look it up for this engine). Look for full scans where an index should be
   used, estimated vs actual row gaps, nested loops over big inputs. Quote the plan line; never just
   claim an index is used.
4. **Use realistic data.** On ten rows the planner picks a full scan anyway. Load data shaped like
   production (distinct values, skew, nulls) where you can, and say what you used.
5. **Prescribe:** the access, its cost growth, plan evidence, cause, and the fix. Adding an index to
   a populated table is a migration; do it without locking the table.

## Report

Open with the budget, before, after, and what was traded. Or, in trace mode: the symptom in the
user's words, the cause in one sentence, and the first thing they'll notice after which phase. Then
a table of kept changes (or phases, or query findings). Profiles and dead ends after.

## Rules

- Never optimize unprofiled code; never report a gain you didn't re-measure.
- An optimization that hides intent gets a one-line comment naming why it exists.

## Common mistakes

Optimizing on a hunch; averages hiding the worst users; several changes at once; unguarded gains
that slip back; micro-optimizing before fixing the algorithm; treating token cost as free; auditing
code nobody complained about; judging a query by milliseconds on seed data.
