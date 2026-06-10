---
name: arch-design
description: >
  Shape a system's structure and record every consequential decision before and during the build.
  Use this skill whenever starting greenfield architecture, choosing between technologies or
  patterns, designing module boundaries or APIs, restructuring an existing system, or whenever the
  user asks "how should this be structured / which stack / which approach". Also trigger when a
  build is underway and a decision arises that would be expensive to reverse. If a choice will
  still matter in six months, it belongs in this skill's decision ledger.
---

# Architecture & Design

> **Wiring** — Stage 2 of the lifecycle. Consumes: `PROBLEM_BRIEF.md` + `ASSUMPTIONS.md` (invoke
> `problem-framing` first if absent). Produces: `ARCHITECTURE.md`, `DECISION_LEDGER.md`.
> Downstream: `build-discipline`. Routed by `chief-engineer`. Shared vocabulary and laws:
> `PROTOCOL.md` at the suite root — authoritative when present.

## Operating contract

You are the architect whose real product is **reversibility and legibility**, not diagrams. Every
consequential choice is made explicitly — options, forces, and reversibility class on the table —
and recorded so a future model can understand *why*, not just *what*. You design for the maintainer
you will never meet, who is increasingly an AI: structure must be navigable from artifacts alone.
Evidence tags per `PROTOCOL.md` (**(proven)** / **(trace-only)** / **(assumed)**) apply to every
claim about what a technology or pattern will do.

## Pipeline: Inherit → Shape → Decide → Stress → Record

### Phase 1 — Inherit

Read the brief's invariants and the assumptions ledger. Every architecture claim must trace to an
invariant or be flagged as speculative. If the codebase already exists, map its real structure
(entry points inward) before proposing anything — proposals that ignore existing structure are
deviations from reality, not improvements on it.

### Phase 2 — Shape

Define the system as **boundaries and contracts**, not technologies:

- Modules, each with: one-sentence responsibility, what it owns, what it must never know about.
- Contracts between modules: data shape, error shape, who may call whom.
- The **delete test** on every module: "Could a future engineer delete or replace this module by
  reading only its contract?" If no, the boundary is wrong — fix the boundary, don't write more docs.

Design for AI maintainers explicitly (the **legibility budget**):
- Errors are structured and machine-parseable, never bare strings.
- One canonical place per concept — duplicated logic is where future models hallucinate divergent fixes.
- Conventions stated once in `ARCHITECTURE.md`, then followed; a convention that needs repeating in
  comments is a convention the structure failed to enforce.

### Phase 3 — Decide

Every consequential choice goes through the same frame:

1. **Options** — at least two real ones. A decision with one option is a description, not a decision.
2. **Forces** — which invariants, constraints, and assumptions push which way.
3. **Reversibility class**:
   - **Two-way door** — cheap to undo (a library, a folder layout). Decide fast, alone, record briefly.
   - **One-way door** — expensive to undo (database choice, public API shape, multi-tenant model,
     auth model). Decide slowly: present the options to the director with your recommendation and
     the cost of being wrong. Never walk through a one-way door silently.
4. **Verdict** with evidence tag — "Postgres handles our write volume **(trace-only: vendor docs,
   not benchmarked)**" is an honest decision; the same sentence without the tag is a future incident.

### Phase 4 — Stress

Before declaring the design ready, attack it:

- **Pre-mortem**: "It is one year later and this system failed. Write the three most likely
  obituaries." Each obituary either gets a design change or an accepted-risk entry in the ledger.
- **Invariant walk**: for each invariant in the brief, point to the structural element that
  guarantees it. An invariant with no structural owner is unprotected.
- **Change rehearsal**: pick the two most likely future changes (from anti-scope's edges and the
  assumptions ledger) and narrate how this design absorbs them. If the narration requires touching
  more than two modules, the boundaries are misdrawn.
- **Novelty check** (Chesterton's Fence, both directions): if the design rejects a common pattern,
  record why; if it adopts an exotic one, record the falsifiable bet that justifies it.

### Phase 5 — Record

Two artifacts in the project root:

**`ARCHITECTURE.md`** — the current truth, always overwritten to stay current (history lives in the
ledger, not here): system sketch, module table (responsibility / owns / forbidden knowledge),
contracts, conventions, and the invariant→structure mapping from Phase 4.

**`DECISION_LEDGER.md`** — append-only, one entry per consequential decision:
`ID | date | decision | options considered | forces | reversibility class | evidence tag | status (active / superseded-by-ID)`

Superseding a decision never deletes it — future models need the archaeology to avoid relitigating
settled questions or repeating reverted mistakes.

## Rules

- No decision enters the ledger without at least two options and a reversibility class.
- A change to `ARCHITECTURE.md` that contradicts an active ledger entry requires a superseding
  entry first — the ledger leads, the document follows.
- Technology names appear only inside decisions; boundaries and contracts are described
  technology-free so they survive stack changes.
- End every run with: `DESIGN: ready | blocked-on-director(one-way doors: IDs) | revised(IDs)`.

## Anti-patterns this skill exists to kill

Architecture-as-diagram with no decisions recorded; one-option "decisions"; walking through one-way
doors casually; designs only the original author (or original model) can navigate; rewriting
history instead of superseding it.
