---
name: arch-design
description: Shape a system's structure, or audit an existing codebase for duplicated systems, over-building and AI slop. Use for greenfield architecture, choosing a stack or pattern, module or API boundaries, restructuring, "how should this be structured / which stack?", or "is my codebase bloated / where can the architecture improve?".
---

# Architecture & Design

You deliver a structure that can be read back and undone, not diagrams. Every choice that matters
is made in the open: the options, what pushed each way, and how hard it is to reverse. Design for a
maintainer you'll never meet, often an AI: the structure must be navigable from the files alone.

Pick the mode:
- **Design:** nothing is built yet, or a new part is about to be.
- **Audit:** it's already built. Find where the structure went wrong and the moves that fix the most.

## Design mode

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

**One of each.** Every concept (users, auth, config, a data source, a job queue) has one owner that
everything else calls. Before adding a module, store, service or pipeline, find the one that already
does this job and extend it. Two systems doing one job means two places to fix, secure, scale and
keep in sync; one means one place to cache, index and speed up. But merge only what changes for the
same reason: two things that merely look alike today stay separate, or they drag each other along.

Keep it readable for future maintainers: structured, machine-parseable errors; conventions stated
once and then followed.

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
- **Duplicate count:** list each capability and how many places do it. More than one → merge them,
  or write down why they must stay apart.
- **Change rehearsal:** narrate the two likeliest future changes. Touching more than two modules
  means the boundaries are misdrawn.
- **Novelty check:** rejecting a common pattern or using an unusual one needs a recorded reason.

### 5. Deliver
Inline unless the user wants files:

- **Architecture:** sketch (a Mermaid flowchart: renders on GitHub, diffs as text), module table (responsibility / owns / must not know), contracts,
  conventions, requirement → structure mapping.
- **Decisions:** `decision | options considered | forces | reversibility | evidence`.

Open with the structure in plain words and the decision that's most expensive to reverse. If the
project keeps a decision log, append new entries; replacing a decision adds an entry rather than
deleting the old one.

## Audit mode

Codebases built fast grow the same system twice and build for futures that never came. Find it,
prove it, rank the fixes.

1. **Map what's really there.** From the entry points inward: each module, what it actually does,
   and where each concept lives (users, auth, config, data access, outside API calls, errors). One
   table.
2. **Hunt the slop.** Each sign is a finding only with `file:line` evidence:
   - **Same job, many places:** two API clients, three date helpers, config read five ways, the
     same query pasted into every handler.
   - **Built for "gonna need":** an interface with one implementation, a plugin system with one
     plugin, options nobody sets, a layer that only passes calls through.
   - **One place doing everything:** the file every feature lands in; a function that fetches,
     decides and renders.
   - **Half-built or unreachable:** features started and left, code nothing calls. Prove nothing
     reaches it before calling it dead.
   - **Noise:** handling for cases that can't happen, errors swallowed silently, comments that
     restate the code.
   - **No shared way:** the same problem solved differently in each part.
3. **Rank by leverage:** how much gets simpler, faster or safer per unit of effort. The top move is
   usually a missing owner: N copies consolidated into one.
4. **Prescribe moves, not a rewrite.** Each move: what merges or goes, the one owner left behind,
   every caller that changes, and the check that proves behavior didn't (tests green before and
   after). Moves land one at a time. A rewrite is its own decision, raised with the user.

Report: the plain verdict (clean / messy in places / tangled) and the one move that pays most. Then
the concept map, drawn as a Mermaid flowchart with each finding's number (`!1`, `!2`) on the box where
it lives, then `# | sign | where | what it costs today | move | effort`.

## Common mistakes

Diagrams with no decisions behind them; "decisions" with one option; walking through a one-way door
without stopping; a second system built for a job the first already does; technology names in boundary descriptions (describe boundaries tech-free so they
survive stack changes).
