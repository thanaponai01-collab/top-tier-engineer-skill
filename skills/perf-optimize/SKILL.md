---
name: perf-optimize
description: >
  Make a working system measurably better along an explicit budget — latency, throughput, memory, cost — and gate the cost class of data access before it ships. Use when the user says something is slow/laggy, asks to "optimize", "speed up", "reduce cost", "make it scale", or asks "is this an N+1 / will this query scale / should I add an index". Never optimize by intuition.
---

# Performance & Optimization

> **The question:** Is it measurably inside budget, with a guard to keep it there?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

if the system cannot be run or profiled here, or the complaint is a felt symptom spanning speed and cohesion, route to `symptom-audit` first — its spec's perf phases then execute under this skill's discipline. The *shape* of stored data changing → `data-evolution` (Phase 3b gates how that shape is accessed, not how it migrates).

## The job

You optimize with a profiler, not an opinion. Nothing changes until the cost is measured, nothing
is claimed until the improvement is measured again under the same conditions, and every gain gets
a guard so it cannot quietly slip back. Correctness comes first: this skill runs only on code that
has passed `correctness-gate`, and every optimization runs the gate again — a fast wrong answer is
worth less than a slow right one. Phase 3b is the one exception, and says so: it judges a plan or a
diff by how its cost *grows*, before there is a budget or a running change to gate, so it precedes
the gate instead of following it and changes nothing while it runs. Evidence rules (per `PROTOCOL.md`) are strict here: a
**(trace-only)** performance claim is a hypothesis, never a result.

## Steps: Budget → Baseline → Profile → Hypothesize → Change-one-thing → Verify → Guard

### Phase 1 — Budget

Optimization with no target never ends. Set or read the budget (in the report, per §3):

`dimension | metric | current | budget | source of budget | guard (test/alert) | status`

Which dimensions count: time as the user experiences it (p50/p95, not averages — an average hides
the users having the worst time), throughput, memory, startup time, binary or bundle size, money
per operation, and **AI cost** (tokens per task, model calls per task, context size per call). On
AI-based systems that last row is often the biggest expense and the least measured. Tie budgets to
acceptance criteria where you can; otherwise mark the budget **(assumed)** and write it down.

### Phase 2 — Baseline

- Reproduce the problem under controlled, recorded conditions: input size, hardware/environment,
  warm vs cold, concurrency. An unrecorded baseline cannot be honestly compared against later.
- Run enough iterations to see variance; report median and spread, never a single run.
- If you can't reproduce the slowness, stop — send it to `evolve-maintain` as missing visibility.
  Optimizing a complaint you cannot reproduce is guessing with extra steps.

### Phase 3 — Profile

Measure where the cost actually is before forming any opinion about where it is. Use the cheapest
tool that will do (a profiler, a query analyzer, timing code, token logging) and record the
biggest contributors. The profile is the only valid source of things to optimize — a hunch may
suggest a *hypothesis to test*, never a target to change.

### Phase 3b — Cost class (data access)

A query that is fast on a thousand rows takes the system down at a million, and you see that in
the query *plan*, not on a stopwatch — so data access is judged by how its cost **grows**, before
any milliseconds are measured. This phase runs on its own, ahead of Phase 1, whenever the request is a
data-access change with no budget yet ("N+1?", "add an index", "will this query scale"); it then
reports its own findings and hands the ones needing a wall-clock number back to Phase 4.

1. **List** every query, ORM call, join and index the change adds or alters, plus every loop or
   collection that *could* run one query per item — taken from the diff and the data-access code,
   never from memory. Note which tables grow as the system is used; on a small fixed lookup table
   none of this matters.
2. **Classify** each access by how its cost grows: **flat** (an indexed lookup of one row), **grows
   with the result** (an index range scan), **grows with the table** (a full scan), or **unbounded**
   (one query per item across a collection, or a join with no selective index). Anything that grows
   with the table, or is unbounded, on a table that keeps growing is a finding *even if it is fast
   today* — today's row count is not tomorrow's. A query inside a loop is one-query-per-item until
   proven otherwise; the fix is a join, a batch fetch, or loading it all up front — say which.
3. **Read the plan, don't time it.** The execution plan decides this: get it from the database
   itself (`EXPLAIN`, `EXPLAIN ANALYZE`, or whatever this engine offers — look it up, don't carry
   tuning habits from another engine) and read it for full scans where an index should have been
   used, confirmation that the index you meant is actually used, large gaps between estimated and
   actual row counts, and nested loops over big inputs. Never claim an index is used — quote the
   plan line. Reading the SQL alone is **(trace-only)**; running the plan is **(proven)**.
4. **Use realistic data, not seed data.** A plan over ten rows tells you nothing — the database
   picks a full scan when the table is tiny. Where you can spin up a throwaway instance, load data
   shaped like the real thing (how many distinct values, how skewed, how many nulls), run the plan
   again, and say what data you used; otherwise the finding caps at **(trace-only)**, naming the
   one `EXPLAIN` that would settle it. An access path that comes back clean is a finding too: it
   says where *not* to spend effort.
5. **Prescribe** for each finding: the access, how its cost grows, the plan evidence and its tag,
   the cause (no index, a query inside a loop, a condition that filters almost nothing, a result
   set with no limit), and a contained fix written in the project's own conventions (Law 5). Adding
   an index to a *populated* table is a schema change — hand that migration to `data-evolution`;
   this phase says which index and why.

### Phase 4 — Hypothesize

For the biggest contributor, state: *"I believe X costs Y because Z; changing it to X′ should cut
the number by roughly W."* A hypothesis with no predicted size cannot be judged afterwards. Try
them in this order, most effective first:
1. **Don't do the work at all** (cache it, skip it, deduplicate it, compute it ahead of time, send
   less context)
2. **Do less work** (a better algorithm, query or data structure; a shorter prompt; batch the calls)
3. **Do the work somewhere else, or later** (async, a queue, load it lazily)
4. **Do the same work faster** (micro-optimization — last resort, and the most complexity added per
   unit gained)

### Phase 5 — Change one thing

One change per measurement. Change two things and you cannot tell which one worked, and a result
nobody can attribute is worse than no result in the record. Each change is its own commit, ready
to revert, naming the hypothesis it tests.

### Phase 6 — Verify

- Re-measure under the *recorded baseline conditions*. Report: predicted vs actual, with spread.
- Re-run `correctness-gate`. An optimization that fails the gate is reverted, not patched in place.
- Record the hypotheses that failed, don't delete them — *"tried X′, expected −40%, got −2%,
  reverted"* is one of the most valuable lines in the record, because it stops the next person
  trying the same dead end.

### Phase 7 — Guard

Every optimization you keep gets a guard before the run ends: a performance test, a budget
assertion, or an alert that fails when the number slips back past budget. Update the budget with
the new current value and a pointer to the guard. A gain with no guard is a temporary gain.

Shape and wording: `PROTOCOL.md` §9. The opening is the budget, the number before, the number now,
and what was traded to get it. The rows are the optimizations kept, one each: the change, before
and after as measured, the guard holding it. Profiles and the dead ends go under `Detail`.

**Verdict noun:** `PERF`

End every run with a `PERF` line (PROTOCOL §5): `done(<budget>: <before> → <after>, guarded)`
carrying the §1 tag — a re-measured gain is the only `done`; `clean(<budget> already met)` when the
baseline was inside budget and nothing changed; `findings(<cost class>: <what grows with what>)`
for a Phase 3b run, which measures and changes nothing; `blocked(unprofilable: …)` when nothing
here can be run or measured.

## When to stop

Stop optimizing — and say so explicitly — when the first of these is true:
1. All budgets are met **(proven)**.
2. The next hypothesis's predicted gain is smaller than its complexity cost (state both).
3. The remaining cost is outside this system's control (network, vendor, physics) — record it as
   a constraint in the architecture decision ledger.

Carrying on past a stop condition is not thoroughness; it is making a working system clever at the
expense of everyone who reads it next.

## Rules

- Never optimize unprofiled code; never report unre-measured gains.
- Pay readability back: any optimization that makes the intent harder to see leaves a one-line
  comment naming the hypothesis that justifies it.

## Common mistakes

Optimizing on a hunch; averages hiding the users having the worst time; several changes at once,
so nothing can be attributed; gains with no guard that slip back within a month; micro-optimizing
before fixing the algorithm; treating token and model-call cost as if it were free; trading
correctness for speed; judging a query by its milliseconds on seed data instead of by how its cost
grows; missing a query inside a loop because each single query looks cheap.
