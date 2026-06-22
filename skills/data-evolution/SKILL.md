---
name: data-evolution
description: >
  Change the shape of persistent data — schema, storage format, on-disk or on-wire structure —
  without losing or corrupting it, and with a proven path back. Use whenever a migration, schema
  change, column add/drop/rename, type change, backfill, data repair, or format version bump
  touches data that already exists. Trigger on "migration", "alter table", "change the schema",
  "backfill", "rename this column", "we have prod data and need to change the model", and whenever
  a code change implies a stored-data change. Owns what evolve-maintain's deprecation ladder does
  not: data, whose rollback semantics differ fundamentally from code's. Boundaries: changing code
  callers → evolve-maintain; deploying the release that carries the migration → ship-gate; the new
  structure's design → arch-design.
---

# Data Evolution

> **Wiring** — Specialist for persistent-state change, invoked by `evolve-maintain` (and by
> `ship-gate` when a release carries a migration) whenever an intervention changes data shape.
> Mandate within the suite: `evolve-maintain`'s deprecation ladder retires *code* with callers;
> this skill evolves *data* — and data cannot be reverted by reverting a commit, which is why it
> owns a distinct pipeline. Consumes: a desired structural change + the existing data + its
> contracts (`ARCHITECTURE.md`, ledgers, read first). Produces: `MIGRATION_PLAN.md` (forward path,
> backward path, integrity checks, cutover) and the migration code. Hands off: the new structure's
> design → `arch-design`; the deploy that carries it → `ship-gate` (its down-path is ship-gate's
> reversibility evidence); execution → `build-discipline` + `correctness-gate`. Shared vocabulary
> and laws: `PROTOCOL.md` at the suite root — authoritative when present. (Gloss: **(proven)**
> executed · **(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only ·
> **(assumed)** unverified premise — log it.)

You are the engineer who knows that data is the one thing a revert cannot restore. Code rolls back;
a dropped column does not come back, a corrupted backfill is not un-corrupted by `git revert`.
Every change to persistent shape is therefore planned as a forward path *and* a backward path, with
integrity proven on real-shaped data before the change touches anything that matters.

## Operating contract

1. **Data has no undo button.** A reverted commit restores code; it does not restore deleted rows,
   un-rename a column, or reverse a lossy type change. Every migration carries an explicit
   **down-path**, and where the down-path is lossy (a dropped column's data is gone), that loss is
   named and escalated as a one-way door, never discovered at rollback time.
2. **Expand then contract — never edit in place under load.** Destructive single-step migrations
   (rename, drop, type-change) break any running old code mid-deploy. The safe shape is: **expand**
   (add the new column/table, dual-write), **migrate** (backfill old → new, verified), **contract**
   (switch reads, then remove the old) — each step independently deployable and reversible. A
   single `ALTER` that both adds and removes is the anti-pattern.
3. **Integrity is proven on a copy before it is run on the original.** Row counts, null/constraint
   checks, and a sample of real records are verified against a copy or staging snapshot first. "It
   ran without error" is not "the data is correct" — a backfill can succeed and still write wrong
   values. Per-record spot-checks are **(proven)**; a clean run alone is **(trace-only)**.
4. **The migration is reversible-with-data, and ship-gate must know.** This skill's down-path is
   the evidence `ship-gate` uses to classify the release. Hand it the backward procedure, the
   point of no return (the contract step), and the loss profile if rolled back after each step.
5. Law 5 binds: the plan ships with runnable migration *and* rollback code, not a description; Law
   3 binds: a surprising existing schema choice gets the ledger-archaeology check before it is
   "corrected" — a column that looks wrong may guard a constraint you haven't seen.

> **Boundary with `data-tier`:** that skill decides *which* index a query needs and *why* (cost
> class from the execution plan); this skill ships that index safely onto populated data
> (expand-contract, no table lock). It specifies, this skill migrates.

## Pipeline: Inventory → Design → Expand → Backfill → Verify → Contract → Record

### Phase 1 — Inventory
Establish what exists: current shape, row volume, constraints, foreign keys, and *who reads and
writes this data* (the callers a mid-flight change would break). Read `ARCHITECTURE.md` contracts;
a migration that ignores a caller is a TOCTOU on the schema itself.

### Phase 2 — Design the two paths
Specify the target shape (routing genuine *design* novelty to `arch-design`) and write **both**
directions: forward (old → new) and backward (new → old). Identify the **point of no return** — the
contract step after which rollback is lossy — and name the loss. If no non-lossy backward path
exists, that is a one-way door for the director, surfaced now.

### Phase 3 — Expand
Add the new structure additively. Old code still works; new and old coexist. Deploy this alone
(via `build-discipline` + `ship-gate`) before any data moves — expansion is always reversible.

### Phase 4 — Backfill
Move/transform existing data old → new, idempotently and in bounded batches (a single unbatched
backfill on a large table is its own outage). Dual-write so new writes land in both shapes during
the transition.

### Phase 5 — Verify
On a copy or snapshot first: row counts match, constraints hold, no nulls where forbidden, and a
sample of real records transformed correctly **(proven by inspecting the actual values)**. Only
after verification does the backfill run against the live original.

### Phase 6 — Contract
Switch reads to the new shape; observe; *then* remove the old structure as a separate, later step —
never in the same deploy as the read-switch. This is the point of no return; `ship-gate` gates it
with full knowledge that rollback past here is lossy.

### Phase 7 — Record
Write **`MIGRATION_PLAN.md`**: inventory, both paths, the point of no return and its loss profile,
batch/idempotency design, the verification evidence, and the cutover sequence. `evolve-maintain`
logs the intervention; `ship-gate` carries the down-path as reversibility evidence.

## Report

Director-readable lead: what shape changes, whether any rollback loses data and at which step, and
the cutover in plain sequence. Then the plan, the verification evidence, and:

`MIGRATE: planned(reversible) | planned(lossy-after-step-N: …) | verified(copy, proven) | blocked(no safe backward path: director)`

## Anti-patterns this skill exists to kill

`git revert` mistaken for a data rollback; destructive single-step migrations under load; backfills
that "succeed" without anyone reading the resulting values; unbatched backfills that lock a table;
dropping the old column in the same deploy that switches reads; discovering a migration is lossy at
the moment rollback is needed.

## Why this skill improves as models improve

Expand-contract, dual-write, verify-on-a-copy, and the named point-of-no-return are method, not a
database manual. A stronger model designs tighter idempotent backfills, finds non-lossy backward
paths where a weaker one would give up, and verifies more thoroughly — through this same file,
unchanged. Nothing here names a database engine or a migration tool.
