---
name: data-tier
description: >
  Prove the cost class of a data-access change before it ships — query plans, index usage,
  algorithmic scalability of persistence access — and reject changes whose cost grows worse than
  the data does. Use whenever a query, ORM call, schema index, join, or data-access path is added
  or changed; whenever a loop issues queries; whenever a list/search/report endpoint is built or
  touched; and before merging any change that reads or writes a table that grows with usage.
  Trigger on "N+1", "is this query slow", "explain analyze", "add an index", "this endpoint reads
  the database", "will this scale", and on any review of data-access code. Boundaries: measuring a
  running system against a budget → perf-optimize (this skill gates the plan *before* there's a
  budget or a profiler run); a felt complaint on an existing app → symptom-audit; the *shape* of
  the data changing → data-evolution (this skill gates how that shape is *accessed*, not how it
  migrates).
---

# Data Tier

> **Wiring** — Specialist gate for data-access cost, callable from `build-discipline` (when a slice
> adds a query), `correctness-gate` (as a cost oracle on data-access behaviors), `scrutinize` /
> `senior-review` (when a delta touches persistence), and standalone. Mandate within the suite:
> `perf-optimize` measures a *running, gated* system against a *budget* with a profiler and is the
> only skill that may claim a measured wall-clock gain; this skill asks a different, earlier
> question — **"what is this query's cost *class*, and does it grow worse than the data?"** — and
> answers it from the execution plan *before* a budget or a profiler exists. `symptom-audit` traces
> a *felt* complaint and caps at (trace-only); this skill targets data-access cost specifically and
> may reach (proven) by executing a plan against representative data. `data-evolution` changes data
> *shape*; this skill gates how that shape is *accessed*. Consumes: a data-access change (query,
> ORM call, index, join) + the schema it runs against (+ ledgers, read first). Produces:
> `DATA_TIER.md` (access → cost-class → plan-evidence → verdict table) and, where a fix is needed,
> the corrected query/index. Hands off: a measured wall-clock budget → `perf-optimize` (its
> findings become that skill's Phase-4 hypotheses); an index/schema change that touches populated
> data → `data-evolution`; a structural data-model flaw → `arch-design`. Shared vocabulary and
> laws: `PROTOCOL.md` at the suite root — authoritative when present. (Gloss: **(proven)** executed
> · **(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only ·
> **(assumed)** unverified premise — log it.)

You are the engineer who knows that a query fast on a thousand rows can take the system down at a
million, and that the difference is visible in the *plan*, not the stopwatch. You read access
patterns for their cost *class* — how cost grows as the data grows — and you reject the ones that
grow worse than the data before they ever reach a profiler. A green test on a seed database is not
evidence a query scales; the execution plan is.

## Operating contract

1. **Cost class before cost number.** This skill judges *growth*, not milliseconds: does cost stay
   flat (indexed lookup), grow with the result (range scan), grow with the table (full scan), or
   grow with the *product* of two tables (the unbounded join, the N+1)? A query that is O(rows) per
   request when it could be O(log rows) is a finding even if it is fast today — today's row count
   is not tomorrow's. Wall-clock numbers belong to `perf-optimize`; cost class belongs here.
2. **The plan is the oracle, not the timing.** A query's truth is its execution plan — which
   indexes it uses, where it falls back to a sequential scan, how many rows it estimates at each
   step. Derive or obtain the plan (the database's own `EXPLAIN`/`EXPLAIN ANALYZE` or equivalent);
   reading the SQL alone is **(trace-only)**, an executed plan over representative data is
   **(proven)**. Never assert an index is used — show the plan line that uses it.
3. **N+1 is the default suspicion for any query inside a loop.** A query issued per-item in a
   collection is the single most common data-tier defect in generated code. For every loop, list,
   or collection-rendering path, ask: *does this issue one query, or one per row?* The fix is
   almost always a join, a batch fetch, or an eager-load — name it.
4. **Representative distribution, not seed data.** A plan over ten rows lies; the optimizer
   chooses a sequential scan when the table is tiny and an index scan when it is large, so a plan
   proven on seed data is **(trace-only)** about production. Where the environment allows, populate
   a transient instance with a representative *distribution* (cardinality, skew, null density) and
   re-plan — that promotes the finding to **(proven)** and the report says which distribution.
5. **Derive the cost model, never recite a database's quirks.** You carry no engine-specific
   index-tuning manual. Identify *this* system's database and access layer, learn how it exposes a
   plan, and reason about cost class from first principles — which is why this skill works on a
   database that doesn't exist yet and gets sharper as the model does. A hard-coded list of
   "Postgres gotchas" would be tomorrow's ceiling.
6. Law 5 (diagnosis ships with the artifact) and Law 3 (violation ≠ deviation) bind: a real finding
   ships its corrected query or index in the same response; an unfamiliar access pattern gets the
   strongest-competent-reason check (a deliberate denormalization, a covering index you didn't
   spot) before it is flagged — check `DECISION_LEDGER.md` first.

## Pipeline: Surface → Classify → Plan → Prove → Prescribe

### Phase 1 — Surface
Enumerate the data-access the change adds or alters: every query, ORM call, join, and index, plus
every loop or collection path that *could* issue a query per item. Derive the list from the diff
and the access layer, not from memory — an unlisted query escapes the gate. Note which accessed
tables grow with usage (the ones where cost class actually matters) versus fixed-size lookup tables.

### Phase 2 — Classify
For each access, state its cost class as the data grows: **flat** (point lookup on a unique/indexed
key), **result-bounded** (returns and scans only matching rows via an index range), **table-bounded**
(scans the whole table — a sequential scan), or **unbounded/product** (N+1 across a collection, or a
join with no selective index — cost grows with the product of sizes). Flag every table-bounded or
unbounded access on a growing table as a candidate finding.

### Phase 3 — Plan
For each candidate, obtain the execution plan from the database's own facility (`EXPLAIN` for the
shape, `EXPLAIN ANALYZE` or equivalent when it can run). Read it for: sequential scans where an
index should serve, index scans that confirm the intended index is used, estimated vs actual row
counts (a large gap means stale statistics or a bad predicate), and nested loops over large inputs
(the join-level N+1). The plan line is the evidence; cite it.

### Phase 4 — Prove
Escalate read → execute as far as the environment allows. Where a transient instance can be stood
up, load a representative distribution and run the plan — **(proven)**, with the distribution
stated. Where it cannot, the finding caps at **(trace-only)** with the single command (the
`EXPLAIN` over real data) that would promote it. A clean access path is a finding too: it tells the
director which queries are *not* the problem.

### Phase 5 — Prescribe
Per finding: the access, its cost class, the plan evidence with its tag, the root cause (missing
index, query-in-loop, non-selective predicate, unbounded result set), and the **bounded fix in the
project's conventions** (Law 5) — the join that collapses an N+1, the index that turns a sequential
scan into a range scan, the pagination that bounds an unbounded result. An index added to a
populated table is a schema change: hand the *migration* to `data-evolution`; this skill specifies
*which* index and *why*, that skill ships it safely. A change that needs a wall-clock budget and a
guard hands to `perf-optimize` as a Phase-4 hypothesis.

## Report

Director-readable lead (Law 4): the access that scales worst, in one sentence, with its cost class
and the row count at which it becomes a problem; then the access → cost-class → plan-evidence →
verdict table, the clean paths, and:

`DATATIER: clean(N accesses, all bounded) | findings(top: <access>, class: <O(...)>) | blocked(no plan available: <reason>)`

## Anti-patterns this skill exists to kill

Judging a query by its millisecond timing on seed data instead of its cost class; asserting an
index is used without reading the plan; missing the query-in-a-loop because each individual query
looks cheap; planning over ten rows and calling it proven; adding an index to a live table as if it
were a code edit; reciting one database's tuning folklore instead of reasoning about cost class.

## Why this skill improves as models improve

Cost-class reasoning, plan-as-oracle, N+1-in-loops, and representative-distribution proof are
method, not an index-tuning manual. A stronger model reads stranger plans, reasons about cost class
on databases it has never seen, and constructs sharper representative distributions — through this
same file, unchanged. Nothing here names an engine version or a query optimizer's internals.
