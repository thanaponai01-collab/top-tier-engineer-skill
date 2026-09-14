---
name: perf-optimize
description: Make a system measurably faster or cheaper, or trace a felt complaint ("navigation takes 3 seconds", "the app feels clunky", "this report takes forever") to its real cause. Also judges whether a query will scale. Use for slow/laggy, "optimize", "speed up", "reduce cost", "make it scale", "is this an N+1 / should I add an index". Never optimize by intuition.
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
5. **Diagnose.** `cause | file:line | what the user feels | proven / traced / suspected`. Several symptoms with
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

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.
