---
name: evolve-maintain
description: >
  Keep a shipped system healthy and able to change safely over time. Use for work on an existing running system: bug reports, incidents, dependency updates, refactors, deprecations, "the system broke / stopped working", or resuming work after a gap.
---

# Maintenance & Evolution

> **The question:** Does it stay healthy, and does it learn from every failure?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## The job

You are the engineer who treats a running system as something with a history and a future, not a
blank page. Every change is classified before it is made, sized by how far it reaches, proven the
same way a brand-new slice would be, and written down so the system's memory outlives any one
conversation or model. The standing rule: at any moment, someone with no chat history must be able
to pick this up safely from the files alone — if they can't, that is itself a defect to fix.

## Steps: Sense → Triage → Treat → Strengthen → Record

### Phase 1 — Sense

Establish what is actually true before touching anything:

- Reproduce the reported behavior **(proven)** or state clearly that you couldn't and what you
  inferred instead **(trace-only)**.
- If the behavior reproduces but the cause is unknown, run `debug-protocol` now — diagnosis is its
  job, and the proven cause it returns is what Phase 2 classifies. Treating a cause nobody proved
  is symptom-patching with extra steps.
- Read what the project already recorded per §3 — architecture, decisions, assumptions, deferred
  work, budgets, past changes — and the recent commits. Symptoms often trace back to an assumption
  that quietly stopped being true, or a TODO whose trigger fired and nobody noticed.
- **Drift check**: do the documents still describe the code? Documents that no longer match the
  code are a finding in their own right — a later reader who trusts a stale `ARCHITECTURE.md` will
  confidently build on something that isn't true.

### Phase 2 — Triage

Classify the intervention; the class determines the rules:

| Class | Meaning | Extra obligations |
|---|---|---|
| **Fix** | Restore intended behavior | Root cause named, regression test added, incident→invariant step (Phase 4) |
| **Adapt** | World changed (dependency, API, OS) | Compatibility surface diffed before upgrading; pin-and-schedule if not now |
| **Migrate** | The shape of stored data changes (schema, format, backfill) | Goes to `data-evolution` — `git revert` does not bring data back; that skill owns the path forward, the path back, expand-then-contract, and the point of no return. Never change a populated schema in place from here |
| **Improve** | Same behavior, better structure | Behavior frozen by tests *before* the refactor; zero observable change is the success criterion |
| **Evolve** | New or changed behavior | Goes through `problem-framing` (criteria) and `arch-design` (decisions) — being in maintenance is not permission to grow the scope |
| **Repay** | A `DEBT_LEDGER.md` row's own trigger fired | Auto-routed here whenever `structure-gate` reports `STRUCTURE: findings(repayment-due: id-hint, signal, current/threshold)` (PROTOCOL §5, §8 rule 2). Contract is §8 rule 4 exactly: extract/split first — the debt pays down before anything else touches the file — then re-lock the baseline at the improved number and move the row from `DEBT_LEDGER.md`'s open table to its Repaid table, same change. Never re-lock to silence the gate without the extraction (§8 rule 3's forbidden move) |

Without this row, a `repayment-due` verdict is a finding with nobody assigned to it. That is the
gap `Repay` closes: `structure-gate` detects, `evolve-maintain` repays, the ledger records it.
Nothing new is being claimed here — the trigger already exists, this class just gives it an owner.

Then work out **how far the change reaches** — modules touched, contracts crossed, data migrated,
callers affected — and match the approach to it: short reach → one direct slice; long reach → a
staged rollout using the deprecation steps below. A "small fix" that reaches a long way has been
classified wrong.

### Phase 3 — Treat

- Work in `build-discipline` slices (plan → build → wire → prove → commit) and close through
  `correctness-gate`. Maintenance gets no exemption from the build rules — most of what rots in an
  old codebase is what "quick fixes" left behind.
- **Cause, not symptom**: a Fix isn't done when the symptom stops; it's done when you can name the
  cause, say why it wasn't caught earlier (no oracle? a guard nothing called? a false assumption?),
  and tag how sure you are of that.
- **Code that looks wrong but was here before you** (Law 3), even under time pressure: check the
  history first. If `DECISION_LEDGER.md` explains it, either respect that decision or replace it
  with a new entry; if nothing explains it, record that nothing did, and proceed with extra proof
  rather than extra confidence.
- **Deprecation ladder** for removing or replacing anything with callers:
  mark → warn → move the callers → remove, with a proven count of remaining callers at each step
  (a code search is **(trace-only)**; runtime evidence is **(proven)**, use it where you can).
  Skipping steps is how weekend outages get made.

### Phase 4 — Strengthen

Every incident makes the system harder to hurt the same way twice:

- **Turn each incident into a rule**: every Fix produces (a) a regression test, and (b) where the
  same kind of failure could happen elsewhere, a new invariant proposed for `PROBLEM_BRIEF.md` or a
  contract change for `ARCHITECTURE.md` — so the whole *kind* of bug dies, not just this one.
- **Missing visibility**: if reproducing it in Phase 1 was hard, add the log, metric, or probe that
  would have made it easy, in the same change.
- **Tidy the records** (on every periodic health check): close or re-trigger stale TODOs, confirm
  or disprove old assumptions, mark decisions that have been replaced, and fix the document drift
  found in Phase 1.

### Phase 5 — Record

Record the intervention — append-only, one entry each, inline or in the project's log per §3:

`ID | date | class | symptom | root cause (evidence tag) | treatment | blast radius | strengthened-by (test/invariant/probe IDs) | follow-ups (TODO IDs)`

The log is written for the next maintainer, who will probably be an AI model. Write entries so a
new symptom can be matched against past causes in one read.

Shape and wording: `PROTOCOL.md` §9. The opening is the symptom in the reporter's own words, the
root cause in one sentence with its §1 tag, and what now stops it coming back. The rows are the log
entry's own columns.

**Verdict noun:** `MAINT <ID>`

End every intervention with a `MAINT <ID>` line (PROTOCOL §5), the ID being the entry's own:
`done(<class>, root cause <tag>, guarded by <test/invariant>)`; `findings(…)` when the treatment is
specified but not landed; `blocked(…)` when it cannot proceed — an unproven root cause is
`blocked(cause unproven: routed to debug-protocol)`.

## Rules

- No intervention proceeds unclassified; no Fix closes without root cause and regression test.
- Reverting is always a legitimate fix — a clean revert plus a ledger entry beats a clever fix
  forward when you aren't sure.

## Common mistakes

Deleting code something still calls; stale documents that mislead the next maintainer; scope
growth disguised as maintenance.
