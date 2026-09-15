---
name: perf-optimize
description: Make a system measurably faster or cheaper, or trace a felt complaint ("navigation takes 3 seconds", "the app feels clunky", "this report takes forever") to its real cause. Also judges whether a query will scale. Use for slow/laggy, "optimize", "speed up", "reduce cost", "make it scale", "is this an N+1 / should I add an index". Never optimize by intuition.
---

# Performance & Optimization

Measure, change one thing, measure again, guard the gain. A fast wrong answer is worth less than a
slow right one, and a gain you only reasoned about is a hypothesis.

Pick the mode:
- **Measure:** it runs here and there's a number to improve.
- **Trace:** a felt complaint, or it can't be run or profiled here.
- **Query scaling:** a data-access change ("N+1?", "add an index?").

## Measure mode

1. **Budget.** `metric | current | target`. User-felt time as p50/p95 (never averages), throughput,
   memory, bundle size, money or tokens per operation. No target given → propose one, mark it assumed.
2. **Baseline.** Several runs under recorded conditions (input size, warm/cold, concurrency); median
   and spread. Can't reproduce the slowness → stop and say what visibility is missing.
3. **Profile.** Only the profile picks targets. A hunch suggests a hypothesis, never a change.
4. **Hypothesize with a size:** "X costs Y because Z; X′ should cut about W." Try in order: don't do
   the work (cache, skip, send less) → do less (algorithm, query, batch) → do it later (async, lazy)
   → do it faster (last).
5. **One change, re-measure, re-test.** Same conditions, predicted vs actual. Broke correctness →
   revert. Record failed attempts so nobody repeats them.
6. **Guard** every kept gain with a test, assertion or alert that fails when it slips.

Stop when budgets are met, the next gain costs more complexity than it's worth, or the rest is out of
this system's control. Say which.

## Trace mode

1. **Pin the symptom** in one sentence: which operation, what the user feels, when.
2. **Trace that path in execution order** from where the framework handles the request. At each step:
   network call? sequential or parallel? cached or recomputed?
3. **Sweep only that path** for work to skip, reduce or defer; anything hiding progress from the user;
   queries or payloads that grow without limit.
4. **Diagnose:** `cause | file:line | what the user feels | proven / traced / suspected`. One cause,
   one row. A clean check is a finding too.
5. **Prescribe in phases** by felt impact per effort, each with what the user should feel after and a
   before/after check. A rewrite is its own decision, never buried in a phase.

## Query-scaling mode

Fast on a thousand rows can be fatal at a million; it shows in the plan, not on a stopwatch.

1. **List** every query, join and index the change adds, and any loop that queries per item.
2. **Classify growth:** flat (indexed lookup), with result, with table (full scan), unbounded (query
   per item). The last two on a growing table are findings **even if fast today**.
3. **Read the plan** (`EXPLAIN ANALYZE` or the engine's equivalent) on realistic data and quote the
   line. Never just claim an index is used.
4. **Prescribe** the fix (join, batch fetch, index). Adding an index to a populated table is a
   migration, not a tweak: `safe-release`.

## Report

Open with before, after and what was traded, or in trace mode the symptom, its cause in one sentence,
and what the user notices after which phase. Then the table. Profiles and dead ends last.
