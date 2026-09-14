---
name: arch-design
description: >
  Shape a system's structure and record every consequential decision before and during a build. Use for greenfield architecture, choosing tech/patterns, module or API boundaries, restructuring, or "how should this be structured / which stack".
---

# Architecture & Design

> **The question:** How is it structured, why, and can each choice be undone?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

*what* to build → `problem-framing` (this skill consumes its invariants, never invents them); executing the design → `build-discipline`; the shape of stored data changing → `data-evolution`.

## The job

You are the architect. What you actually deliver is a structure that can be undone and read back
later, not diagrams. Every choice that matters is made in the open — the options, what pushed each
way, and how hard it is to reverse — and written down so a later reader knows *why*, not just
*what*. You are designing for a maintainer you will never meet, more and more often an AI: the
structure has to be navigable from the files alone.
Evidence tags per `PROTOCOL.md` (**(proven)** / **(trace-only)** / **(assumed)**) apply to every
claim about what a technology or pattern will do.

## Steps: Inherit → Shape → Decide → Stress → Record

### Phase 1 — Inherit

Read the brief's invariants and the assumptions ledger. Every architecture claim must trace to an
invariant or be flagged as speculative. If the codebase already exists, map its real structure
(entry points inward) before proposing anything — a proposal that ignores the structure that is already
there is not an improvement on reality, just a departure from it.

### Phase 2 — Shape

Define the system as **boundaries and contracts**, not technologies:

- Modules, each with: one-sentence responsibility, what it owns, what it must never know about.
- Contracts between modules: data shape, error shape, who may call whom.
- The **delete test** on every module: "Could a future engineer delete or replace this module by
  reading only its contract?" If no, the boundary is wrong — fix the boundary, don't write more docs.

Design for AI maintainers on purpose — the system has to stay readable:
- Errors are structured and machine-parseable, never bare strings.
- One place per concept — when the same logic lives in two places, later readers fix one and miss the other.
- Conventions stated once in `ARCHITECTURE.md`, then followed; a convention that needs repeating in
  comments is a convention the structure failed to enforce.

### Phase 3 — Decide

Every consequential choice goes through the same frame:

1. **Options** — at least two real ones, and one of them is the **simplest thing that satisfies
   every invariant**. A decision with one option is a description, not a decision; and two options of
   the same weight (Postgres vs SQLite) is the same failure dressed up as a comparison, because
   the plain version is the one that reliably never gets considered. Adopt it, or name the invariant
   that kills it. Taking it is not settling — it is the measured starting point you buy anything
   more complex from, and `perf-optimize` has nothing to compare against without one.
2. **Forces** — which invariants, constraints, and assumptions push which way.
3. **Reversibility class**:
   - **Two-way door** — cheap to undo (a library, a folder layout). Decide fast, alone, record briefly.
   - **One-way door** — expensive to undo (database choice, public API shape, multi-tenant model,
     auth model). Decide slowly: present the options to the director with your recommendation and
     the cost of being wrong. Never walk through a one-way door silently.
4. **The dependency bar** (DECISION_LEDGER D002) — adding a dependency is itself a consequential
   decision, and usually a one-way door in disguise: it brings upgrades you have to keep
   up with, code you did not write, a style you now have to follow, and a new way to break. A new dependency enters the ledger only with: (a) the
   approximate cost of writing the needed slice ourselves, (b) the fraction of the library's
   surface we will actually use, (c) its maintenance pulse (recent releases, open security issues)
   **(trace-only at minimum)**, (d) its license and whether that license is compatible with this
   project's, and (e) the pin/lock plan. Default: if we would use under ~10% of it, or could write
   the part we need in under ~100 lines, write it — simple code you own outlasts complex code you
   borrowed.
5. **The complexity bar** — Rule 4 pointed at ourselves. Nothing above prices complexity we build
   *ourselves*, so importing a library needs five pieces of evidence while inventing a registry, a
   plugin seam, or an extra layer needs none — and the harm is just as real on our side. So any new
   structure of our own enters the ledger with the callers it has **today** (counted, not imagined)
   and the invariant that pays for it. Default, mirroring Rule 4: **one caller and
   an inline version under ~100 lines → inline it.**
6. **Verdict** with evidence tag — "Postgres handles our write volume **(trace-only: vendor docs,
   not benchmarked)**" is an honest decision; the same sentence without the tag is a future incident.

### Phase 4 — Stress

Before declaring the design ready, attack it:

- **Pre-mortem**: "It is one year later and this system failed. Name the three most likely
  reasons." Each reason either gets a design change or an accepted-risk entry in the ledger.
- **Invariant walk**: for each invariant in the brief, point to the structural element that
  guarantees it. An invariant with no structural owner is unprotected.
- **Change rehearsal**: pick the two most likely future changes (from anti-scope's edges and the
  assumptions ledger) and narrate how this design absorbs them. If the narration requires touching
  more than two modules, the boundaries are misdrawn.
- **Novelty check**, both directions (Law 3): if the design rejects a common pattern, record why;
  if it uses an unusual one, record the bet that justifies it, in terms that could be proven wrong.

### Phase 5 — Record

Two artifacts — inline in the report under their own headings, or as files when §3 warrants:

**`ARCHITECTURE.md`** — the current truth, restated in full each time rather than patched (history
lives in the ledger, not here): system sketch, module table (responsibility / owns / forbidden
knowledge), contracts, conventions, and the invariant→structure mapping from Phase 4.

**`DECISION_LEDGER.md`** — one entry per consequential decision, never edited once written:
`ID | date | decision | options considered | forces | reversibility class | evidence tag | status (active / superseded-by-ID)`

Replacing a decision never deletes it — later readers need the history so they do not re-argue
settled questions or repeat a mistake that was already undone.

Shape and wording: `PROTOCOL.md` §9. The opening says what the structure is in the director's own
words and names the decision here that is most expensive to reverse. The rows are the consequential
decisions, in the ledger's columns. Where the two artifacts stay inline, they go under `Detail`.

**Verdict noun:** `DESIGN`

End every run with a `DESIGN` line (PROTOCOL §5): `done(<N> decisions, <M> one-way doors)` carrying
the §1 tag; a one-way door the director must rule on is `blocked(one-way door: …)`.

## Rules

- No decision enters the ledger without at least two options and a reversibility class.
- A restatement of the architecture that contradicts an active ledger entry requires a superseding
  entry first — the ledger leads, the document follows.
- Technology names appear only inside decisions; boundaries and contracts are described
  technology-free so they survive stack changes.

## Common mistakes

Diagrams with no decisions recorded behind them; "decisions" with only one option; walking through
a one-way door without stopping; designs only the person (or model) who wrote them can navigate;
rewriting history instead of adding the entry that replaces it.
