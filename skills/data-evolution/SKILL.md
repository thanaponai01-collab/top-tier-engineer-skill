---
name: data-evolution
description: >
  Change the shape of persistent data — schema, storage format, on-disk/wire structure — without losing it, with a proven path back. Trigger on "migration", "alter table", "change the schema", "backfill", "rename this column".
---

# Data Evolution

> **The question:** How does stored data change shape without losing any, and with a way back?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

changing code callers → `evolve-maintain`; deploying the release that carries the migration → `ship-gate`; the new structure's design → `arch-design`; how the new shape is *accessed* → `perf-optimize` Phase 3b.

## The job

You are the engineer who knows that data is the one thing a revert cannot bring back. Code rolls
back; a dropped column does not come back, and `git revert` does not un-corrupt a bad backfill. So
every change to the shape of stored data is planned as a way forward *and* a way back, with the
data proven intact on a realistic copy before the change touches anything that matters.

1. **Data has no undo button.** A reverted commit restores code; it does not restore deleted rows,
   un-rename a column, or reverse a lossy type change. Every migration carries an explicit
   **down-path**, and where the down-path is lossy (a dropped column's data is gone), that loss is
   named and escalated as a one-way door, never discovered at rollback time.
2. **Expand, then contract — never change in place on a live system.** A destructive one-step
   migration (rename, drop, change a type) breaks whatever old code is still running mid-deploy.
   The safe shape is: **expand** (add the new column or table, write to both), **migrate** (copy
   old → new, verified), **contract** (switch reads over, then remove the old) — each step deployed
   and reversed on its own. A single `ALTER` that both adds and removes is the mistake to avoid.
3. **Prove it on a copy before running it on the original.** Check row counts, nulls and
   constraints, and read a sample of real records — on a copy or a staging snapshot first. "It ran
   without error" is not the same as "the data is right": a backfill can finish cleanly and still
   write wrong values. Checking actual records is **(proven)**; a clean run on its own is
   **(trace-only)**.
4. **The migration has to be reversible with the data intact, and ship-gate has to know.** The way
   back that you write here is the evidence `ship-gate` uses to classify the release. Hand it the
   backward procedure, the point of no return (the contract step), and what would be lost if it
   were rolled back after each step.
5. Law 5 applies: the plan ships with migration *and* rollback code you can actually run, not a
   description of them. Law 3 applies: a schema choice that looks odd gets checked against the
   history before you "correct" it — a column that looks wrong may be holding up a constraint you
   have not seen.

> **Boundary with `perf-optimize` Phase 3b:** that phase decides *which* index a query needs and
> *why* (cost class from the execution plan); this skill ships that index safely onto populated
> data (expand-contract, no table lock). It specifies, this skill migrates.

## Steps: Inventory → Design → Expand → Backfill → Verify → Contract → Record

### Phase 1 — Inventory
Establish what exists: current shape, row volume, constraints, foreign keys, and *who reads and
writes this data* (the callers a mid-deploy change would break). Read the contracts in
`ARCHITECTURE.md`: a migration that misses a caller changes the schema out from under code that is
still using the old one.

### Phase 2 — Design the two paths
Specify the target shape (routing genuine *design* novelty to `arch-design`) and write **both**
directions: forward (old → new) and backward (new → old). Identify the **point of no return** — the
contract step after which rollback is lossy — and name the loss. If no non-lossy backward path
exists, that is a one-way door for the director, surfaced now.

### Phase 3 — Expand
Add the new structure additively. Old code still works; new and old coexist. Deploy this alone
(via `build-discipline` + `ship-gate`) before any data moves — expansion is always reversible.

### Phase 4 — Backfill
Copy or transform existing data old → new, in batches, and written so that re-running it is safe
(one unbatched backfill on a large table is an outage of its own). Write to both shapes during the
transition, so nothing new is missed.

### Phase 5 — Verify
On a copy or snapshot first: row counts match, constraints hold, no nulls where forbidden, and a
sample of real records transformed correctly **(proven by inspecting the actual values)**. Only
after verification does the backfill run against the live original.

### Phase 6 — Contract
Switch reads to the new shape; observe; *then* remove the old structure as a separate, later step —
never in the same deploy as the read-switch. This is the point of no return; `ship-gate` gates it
with full knowledge that rollback past here is lossy.

### Phase 7 — Record
Record the migration plan — inline, or as a file when §3 warrants one: inventory, both
paths, the point of no return and its loss profile,
batch/idempotency design, the verification evidence, and the cutover sequence. `evolve-maintain`
logs the intervention; `ship-gate` carries the down-path as reversibility evidence.

## Report

Shape and wording: `PROTOCOL.md` §9. The opening says what shape changes, whether any rollback
loses data and at which step, and the cutover in plain sequence.

The rows are the migration steps, one each: step, forward action, backward action, lossy from here.
The plan and the verification evidence go under `Detail`.

**Verdict noun:** `MIGRATE`

a `MIGRATE` line (PROTOCOL §5) — `done` states reversible or lossy-after-step-N and carries the §1 tag; no safe backward path is `blocked(one-way door: …)`.

## Common mistakes

Treating `git revert` as a way to roll back data; destructive one-step migrations on a live
system; backfills that "succeed" with nobody reading the values they wrote; unbatched backfills
that lock a table; dropping the old column in the same deploy that switches reads; finding out a
migration loses data at the moment you need to roll it back.
