---
name: symptom-audit
description: >
  Trace a user's felt complaint about an EXISTING codebase — "navigation takes 2–3 seconds",
  "saving is slow", "the app feels clunky", "this report takes forever" — to its evidenced causes
  in the source, and deliver a phased prescription ordered by impact-per-effort. Use whenever a
  complaint about a working system arrives with a codebase that can be read but not necessarily
  run, profiled, or gated in this environment; whenever the complaint spans categories (speed AND
  coherence AND UX); and whenever the deliverable is a spec for someone else to execute rather
  than an executed change. Boundaries: broken/wrong output → debug-protocol; runnable system with
  a single measurable budget → perf-optimize directly; "is this codebase good?" with no symptom →
  senior-review; "nothing happens at all" → wire-check.
---

# Symptom Audit

> **Wiring** — Diagnostic front-end for complaints about existing systems. Mandate within the
> suite: `debug-protocol` asks *"why is it wrong?"*; `perf-optimize` asks *"is it measurably
> within budget?"* and is the **only** skill that may claim a measured gain; this skill asks
> **"where does the felt complaint live, and what is the cheapest ranked path to relief?"** —
> and it may answer from source alone. Consumes: an existing codebase + a felt complaint
> (+ ledgers, read first). Produces: `AUDIT_SPEC.md` — the diagnosis table and phased
> prescription. Hands off: prescription phases → `build-discipline` to execute; perf phases run
> under `perf-optimize` discipline (this skill's findings become its Phase-4 hypotheses, its
> budgets land in `PERF_BUDGET.md`); anything found *broken* mid-trace → `debug-protocol`;
> missing connections → `wire-check`; rewrite-scale causes → director via `arch-design`, never
> smuggled into the spec. Shared vocabulary and laws: `PROTOCOL.md` at the suite root —
> authoritative when present. (Gloss: **(proven)** executed · **(trace-only)** read, chain
> complete · **(suspected)** chain incomplete, flag only · **(assumed)** unverified premise —
> log it.)

One principle, everything else serves it: **diagnose by following the user's actual complaint
through the system's execution order, prove every claim against the source, and only then
prescribe — ordered by what the user will feel soonest.**

## Operating contract

1. **Symptom dictates scope.** The user's words are the spec for what to investigate. Pin the
   precise symptom first — "2–3 seconds before it moves to another page" is *navigation*, not
   save, not load — and that single sentence decides which path is traced and which sweep
   categories are even relevant. Auditing what the user didn't complain about is wasted motion;
   if something alarming-but-off-symptom surfaces, it is one flagged line routed to its owning
   skill, never a second audit.
2. **Follow the lifecycle, not the file tree.** A codebase has hundreds of files; any single
   complaint executes a handful. Never read everything — identify the path that runs during the
   slow/clunky operation and read those files **in the order they execute**. The file tree is for
   orientation; the execution order is what gets read. This is what keeps an audit fast and
   focused instead of a vague tour.
3. **Evidence or it doesn't enter the report.** Every finding cites file and, wherever possible,
   line, tagged per `PROTOCOL.md` — in this environment most findings honestly cap at
   **(trace-only)**, and the report says so rather than borrowing `perf-optimize`'s authority.
   A suspicion is not a finding until the source confirms it. And a **clean check is also a
   finding** — it tells the user where *not* to spend effort.
4. **Prescribe by impact-per-effort, never by rewrite.** Findings before fixes. The cheapest
   change with the biggest *felt* difference goes first — perceived-speed fixes almost always
   lead. Every fix is a bounded diff to the existing architecture, written in the project's own
   conventions, with explicit out-of-scope lines to prevent creep. A cause solvable only by
   rewrite is escalated as a separate decision (see Wiring), not hidden inside phase 3 of a spec.
5. Law 5 (diagnosis ships with the artifact) applies in full: the prescription carries exact
   code, not homework. Law 3 (violation ≠ deviation) guards the sweep: an unfamiliar pattern on
   the traced path is a question or a `REVIEW_LEDGER.md` entry, never an automatic finding.

## Pipeline: Symptom → Map → Trace → Sweep → Diagnose → Prescribe → Pre-verify

### Phase 1 — Symptom
Extract the precise complaint in one sentence: the operation, the felt cost, the conditions. If
it cannot be pinned to an operation ("everything is just bad"), ask one narrowing question or
audit the single most-used flow, stating that choice **(assumed)**. This sentence heads
`AUDIT_SPEC.md`; everything below must trace back to it.

### Phase 2 — Map
Orient before tracing: read the manifest for the stack, the project's own docs/ledgers for its
conventions and rules, and identify **this framework's lifecycle entry point** — the only
stack-specific knowledge the audit needs. List the candidate path for the symptom's operation;
read nothing deeply yet.

### Phase 3 — Trace
Read the execution path for the symptom's operation, in run order, building a causality model as
you go — for performance: *is each step a network hop? serial or parallel? cached or recomputed?*
"Slow navigation" traces the request path; "saving is slow" traces the mutation path; "the report
is wrong-ish/stale" traces the data path. Anything found actually *broken* here reroutes (see
Wiring) — this skill audits working systems that feel bad.

### Phase 4 — Sweep
Run category checks **against the traced path only**. For performance complaints:
- **Perceived** — does anything block the user from seeing progress?
- **Latency** — redundant or serial round trips that could be parallel or absent?
- **Volume** — does any query/payload grow unbounded with usage (the "fine in week 1, dead in
  month 3" class)?
- **Waste** — recomputing or re-invalidating more than necessary?
- **Locality** — is compute far from its data?

For cohesion/UX complaints: duplicated primitives, state that dies on navigation, dead-end flows,
missing global shortcuts. These checklists are the **swappable part** of this skill: the skeleton
(symptom → trace → evidence → ranked prescription) is audit-type-agnostic; a security or
accessibility audit swaps in its own category list here and changes nothing else.

### Phase 5 — Diagnose
Assemble the table — `cause → location (file:line) → felt cost → tag` — causes before cures.
Multiple symptoms sharing one root cause collapse to one row; that collapse is often the
audit's chief insight.

### Phase 6 — Prescribe
The phased spec, per contract Rule 4: each phase = bounded diff(s) with exact code in the
project's conventions, the cause rows it resolves, an explicit out-of-scope line, and its
predicted felt effect. Order phases by impact-per-effort, not by code location.

### Phase 7 — Pre-verify
This skill does not claim the improvement — it makes the claim **checkable**. Every phase ships
with its observable before/after check pre-written: the measurement `perf-optimize` will run as
budget/baseline, or the behavior `correctness-gate` will assert. A prescription whose success
can't be observed is an opinion with formatting.

## Report

Director-readable lead (Law 4): the symptom in their words, the one-sentence root story, the
first thing they'll feel and after which phase. Then the diagnosis table, the phased spec, the
clean checks, and the verdict line:

`AUDIT: prescribed(N phases, top: <fix>) | clean(traced path healthy) | rerouted(to <skill>: <reason>) | blocked(symptom unpinnable)`

## Anti-patterns this skill exists to kill

The vague grand tour (reading the file tree instead of the execution path); auditing what nobody
complained about; findings without file:line; reporting only problems and never the clean checks;
prescriptions ordered by where code lives instead of what the user feels; the smuggled rewrite;
specs with no observable success condition; claiming measured gains from a read-only trace.

## Why this skill improves as models improve

Nothing here encodes a stack: symptom-sets-scope, trace-in-run-order, evidence-or-silence,
rank-by-felt-impact are method. Phase 2 deliberately learns the stack and lifecycle fresh each
time, so the same reasoning machine runs against a Rails app, a Go service, or a React SPA — a
stronger model pins sharper symptoms, traces deeper paths, and writes tighter bounded diffs,
through this same file, unchanged.
