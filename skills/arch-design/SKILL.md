---
name: arch-design
description: Shape a system's structure and make every consequential decision in the open, with options and reversibility. Use for greenfield architecture, choosing a stack or pattern, module or API boundaries, restructuring, or "how should this be structured / which stack?".
---

# Architecture & Design

You deliver a structure that can be read back and undone, not diagrams. Every choice that matters
is made in the open: the options, what pushed each way, and how hard it is to reverse. Design for a
maintainer you'll never meet, often an AI: the structure must be navigable from the files alone.

## Phases

### 1. Inherit
Read the requirements (ask for them, or state the ones you're assuming). Every structural claim
traces to a requirement or is flagged as speculative. If code exists, map its real structure from
the entry points inward before proposing anything.

### 2. Shape
Define the system as **boundaries and contracts**, not technologies:
- Modules, each with a one-sentence responsibility, what it owns, and what it must never know.
- Contracts between modules: data shape, error shape, who may call whom.
- **Delete test:** could someone replace this module by reading only its contract? If not, fix the
  boundary.

Keep it readable for future maintainers: structured, machine-parseable errors; one place per
concept; conventions stated once and then followed.

### 3. Decide
Every consequential choice goes through this frame:

1. **At least two real options**, one of which is the **simplest thing that meets every
   requirement**. Adopt it, or name the requirement that rules it out.
2. **Forces:** which requirements and constraints push which way.
3. **Reversibility:**
   - *Two-way door* (a library, folder layout): decide fast, note briefly.
   - *One-way door* (database, public API shape, tenancy model, auth model): present options, a
     recommendation, and the cost of being wrong to the user. Never walk through silently.
4. **Dependency bar.** A new dependency needs: rough cost to write the needed part yourself, the
   fraction of the library you'd use, maintenance health (recent releases, open security issues),
   license compatibility, and a pin plan. Default: under ~10% used, or under ~100 lines to write →
   write it.
5. **Complexity bar.** A new layer, registry or plugin seam of your own needs the callers it has
   **today** (counted) and the requirement that pays for it. One caller and under ~100 lines →
   inline it.
6. **Say how you know.** "Postgres handles our write volume (vendor docs, not benchmarked)" is
   honest; the same sentence without the source is a future incident.

### 4. Stress
- **Pre-mortem:** "A year later this failed. Name the three likeliest reasons." Each gets a design
  change or an accepted risk.
- **Requirement walk:** point to the structural element that guarantees each invariant. One with
  no owner is unprotected.
- **Change rehearsal:** narrate the two likeliest future changes. Touching more than two modules
  means the boundaries are misdrawn.
- **Novelty check:** rejecting a common pattern or using an unusual one needs a recorded reason.

### 5. Deliver
Inline unless the user wants files:

- **Architecture:** sketch, module table (responsibility / owns / must not know), contracts,
  conventions, requirement → structure mapping.
- **Decisions:** `decision | options considered | forces | reversibility | evidence`.

Open with the structure in plain words and the decision that's most expensive to reverse. If the
project keeps a decision log, append new entries; replacing a decision adds an entry rather than
deleting the old one.

## Common mistakes

Diagrams with no decisions behind them; "decisions" with one option; walking through a one-way door
without stopping; technology names in boundary descriptions (describe boundaries tech-free so they
survive stack changes).
