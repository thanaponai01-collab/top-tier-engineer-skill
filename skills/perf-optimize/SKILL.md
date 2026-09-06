---
name: perf-optimize
description: >
  Make a working system measurably better along an explicit budget — latency, throughput, memory, cost — and gate the cost class of data access before it ships. Use when the user says something is slow/laggy, asks to "optimize", "speed up", "reduce cost", "make it scale", or asks "is this an N+1 / will this query scale / should I add an index". Never optimize by intuition.
---

# Performance & Optimization

> **Asks:** Is it measurably within budget, and guarded there?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## Boundaries

if the system cannot be run or profiled here, or the complaint is a felt symptom spanning speed and cohesion, route to `symptom-audit` first — its spec's perf phases then execute under this skill's discipline. The *shape* of stored data changing → `data-evolution` (Phase 3b gates how that shape is accessed, not how it migrates).

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

Optimization without a target never terminates. Establish or read the budget (inline per §3):

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

### Phase 3b — Cost class (data access)

A query fast on a thousand rows takes the system down at a million, and the difference is visible
in the *plan*, not the stopwatch — so data access is judged by how its cost **grows**, before any
millisecond is measured. This phase runs on its own, ahead of Phase 1, whenever the request is a
data-access change with no budget yet ("N+1?", "add an index", "will this query scale"); it then
reports its own findings and hands the ones needing a wall-clock number back to Phase 4.

1. **Surface** every query, ORM call, join and index the change adds or alters, plus every loop or
   collection path that *could* issue a query per item — from the diff and the access layer, never
   from memory. Note which tables grow with usage; on a fixed-size lookup table cost class is moot.
2. **Classify** each access as **flat** (indexed point lookup), **result-bounded** (index range
   scan), **table-bounded** (sequential scan) or **unbounded/product** (N+1 across a collection, or
   a join with no selective index). Table-bounded or unbounded on a growing table is a candidate
   finding *even if it is fast today* — today's row count is not tomorrow's. A query inside a loop
   is N+1 until proven otherwise; the fix is a join, a batch fetch, or an eager-load — name it.
3. **Plan, don't time.** The execution plan is the oracle: obtain it from the database's own
   facility (`EXPLAIN`, `EXPLAIN ANALYZE`, or this engine's equivalent — derive it, carry no
   engine-specific tuning folklore) and read it for sequential scans where an index should serve,
   confirmation that the intended index is used, estimate-vs-actual row gaps, and nested loops over
   large inputs. Never assert an index is used — cite the plan line. Reading the SQL alone is
   **(trace-only)**; an executed plan is **(proven)**.
4. **Representative distribution, not seed data.** A plan over ten rows lies — the optimizer picks a
   sequential scan when the table is tiny. Where a transient instance can be stood up, load a
   representative distribution (cardinality, skew, null density), re-plan, and say which
   distribution; otherwise the finding caps at **(trace-only)** with the one `EXPLAIN` that would
   promote it. A clean access path is a finding too: it says where *not* to spend effort.
5. **Prescribe** per finding: the access, its cost class, the plan evidence and its tag, the root
   cause (missing index, query-in-loop, non-selective predicate, unbounded result set), and the
   bounded fix in the project's conventions (Law 5). An index added to a *populated* table is a
   schema change — hand the migration to `data-evolution`; this phase specifies which index and why.

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
or alert that fails when the metric regresses past budget. Update the budget (new current,
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

## Anti-patterns this skill exists to kill

Optimizing by vibes; averages hiding tail pain; stacked changes with unattributable results;
unguarded gains that regress in a month; micro-optimizing before algorithm-level wins; treating
token/inference cost as invisible; sacrificing correctness for speed; judging a query by its
milliseconds on seed data instead of its cost class; missing the query-in-a-loop because each
individual query looks cheap.
