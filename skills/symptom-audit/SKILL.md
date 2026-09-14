---
name: symptom-audit
description: >
  Trace a user's felt complaint about an EXISTING codebase — "navigation takes 2–3 seconds", "saving is slow", "the app feels clunky", "this report takes forever" — to evidenced causes, and deliver a phased prescription ordered by impact-per-effort.
---

# Symptom Audit

> **The question:** Where does the complaint actually come from, and what is the cheapest fix?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

broken/wrong output → `debug-protocol`; runnable system with a single measurable budget → `perf-optimize` directly; "is this codebase good?" with no symptom → `senior-review`; dead code/layer breaches with no symptom → `latent-audit`; "nothing happens at all" → `wire-check`.

One principle, and everything else serves it: **follow the user's actual complaint through the
code in the order it runs, prove every claim against the source, and only then prescribe fixes —
ordered by what the user will notice soonest.**

## The job

1. **The symptom sets the scope.** The user's words are the spec for what to look at. Pin down the
   exact symptom first — "2–3 seconds before it moves to another page" is *navigation*, not saving
   and not loading — and that one sentence decides which path you trace and which checks are even
   relevant. Auditing what the user did not complain about is wasted work; if something alarming
   but unrelated turns up, it is one flagged line sent to the skill that owns it, never a second
   audit.
2. **Follow what runs, not the folder structure.** A codebase has hundreds of files; any one
   complaint runs through a handful. Never read everything — find the path that runs during the
   slow or clunky operation and read those files **in the order they execute**. The folder
   structure is for getting oriented; the execution order is what you actually read. This is what
   keeps an audit fast and focused instead of a vague tour.
3. **No evidence, no entry in the report.** Every finding cites a file and, wherever possible, a
   line, tagged per `PROTOCOL.md`. In this kind of audit most findings honestly stop at
   **(trace-only)**, and the report says so instead of borrowing the authority of a real
   measurement from `perf-optimize`. A suspicion is not a finding until the source confirms it.
   And a **check that came back clean is also a finding** — it tells the user where *not* to spend
   effort.
4. **Order fixes by impact for effort, and never by rewriting.** Findings come before fixes. The
   cheapest change with the biggest *felt* difference goes first — fixes that make it feel faster
   almost always lead. Every fix is a contained change to the existing architecture, written in the
   project's own conventions, with explicit out-of-scope lines so it doesn't creep. A cause that
   can only be fixed by a rewrite is raised as its own decision, not buried in phase 3 of a spec.
5. Law 5 applies in full: the prescription carries exact code, not homework. Law 3 guards the
   sweep: a pattern on the traced path that you simply don't recognise is a question, or an entry
   in `REVIEW_LEDGER.md` — never an automatic finding.

## Steps: Symptom → Map → Trace → Sweep → Diagnose → Prescribe → Pre-verify

### Phase 1 — Symptom
Write the exact complaint in one sentence: the operation, what it costs the user, and when it
happens. If it cannot be pinned to an operation ("everything is just bad"), ask one narrowing
question, or audit the single most-used flow and mark that choice **(assumed)**. This sentence
heads the audit, and everything below has to trace back to it.

### Phase 2 — Map
Get oriented before tracing: read the manifest to see the stack, the project's own docs and
ledgers for its conventions, and find **where this framework starts handling a request** — the
only stack-specific thing the audit needs to know. List the likely path for the operation in the
complaint; don't read anything deeply yet.

### Phase 3 — Trace
Read the path the operation runs through, in the order it runs, building up a picture of what
causes what — for speed complaints: *is this step a network call? does it run one after another or
at the same time? is it cached or recomputed?* "Navigation is slow" traces the request path;
"saving is slow" traces the write path; "the report looks stale or wrong" traces the data path.
Anything actually *broken* that you find here gets rerouted — this skill audits working systems
that feel bad.

### Phase 4 — Sweep
Run the category checks **against the traced path only**. For speed complaints, check the traced
path against `perf-optimize`'s order of leverage (Phase 4) — work that could be skipped, reduced,
moved later, or made faster — plus two this skill adds, because they are felt rather than
measured: **how it feels** (is anything stopping the user from seeing progress?) and **growth**
(does any query or payload grow without limit as the system is used — the "fine in week 1, dead in
month 3" kind?). When the suspect is one query's cost, `perf-optimize` Phase 3b proves it from the
execution plan; this sweep flags the symptom, that phase settles it.

For complaints about the experience hanging together: duplicated building blocks, state that is
lost when the user navigates, flows that dead-end, missing global shortcuts. These lists are the
**replaceable part** of this skill: the frame (symptom → trace → evidence → ranked prescription)
works for any kind of audit; a security or accessibility audit swaps in its own list here and
changes nothing else.

### Phase 5 — Diagnose
Build the table — `cause → location (file:line) → what the user feels → tag` — causes before
fixes. Several symptoms with one shared cause collapse into one row, and that collapse is often
the most valuable thing in the audit.

### Phase 6 — Prescribe
The phased spec, per Rule 4: each phase is one or more contained changes, with exact code in the
project's conventions, the cause rows it resolves, an explicit out-of-scope line, and what the
user should feel afterwards. Order the phases by impact for effort, not by where the code lives.

### Phase 7 — Pre-verify
This skill does not claim the improvement — it makes the claim **checkable**. Every phase ships
with its before/after check already written: the measurement `perf-optimize` will run as its
baseline, or the behavior `correctness-gate` will assert. A prescription whose success nobody can
observe is an opinion in a table.

## Report

Shape and wording: `PROTOCOL.md` §9. The opening carries the symptom in the user's own words, the
cause in one sentence, and the first thing they will notice — and after which phase.

The rows are the phases, one each: phase, the cause it removes, the evidence, what the user feels
once it lands. The full spec per phase and the checks that came back clean go under `Detail`.

**Verdict noun:** `AUDIT`

an `AUDIT` line (PROTOCOL §5) — a prescription is `findings(N phases, top: <fix>)`; a reroute is `blocked(rerouted to <skill>: <reason>)`.

## Common mistakes

The vague grand tour — reading the folder structure instead of the path that runs; auditing what
nobody complained about; findings with no file:line; reporting only problems and never the checks
that came back clean; fixes ordered by where the code lives instead of by what the user feels; a
rewrite slipped in quietly; specs with no observable way to tell if they worked; claiming measured
gains from a trace where nothing was run.
