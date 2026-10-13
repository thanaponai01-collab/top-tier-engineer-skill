---
name: arch-design
description: >-
  Improve or design a codebase's architecture, shown as before/after pictures. Use for "could the architecture be better?", "how should this be structured?"
metadata:
  stage: design
  card: "could the architecture be better? how should it be structured?"
---

# Architecture & Design

Take a codebase to a simpler, better-shaped place: the smallest structure that does the job,
navigable from the files alone by a maintainer you'll never meet, often an AI. The reader may not
read code; owners often only feel symptoms (checkout is slow, a small change takes a week). Show
what hurts, which chain of calls causes it, and what better looks like, in pictures and plain
words; engineers get the same story plus `file:line`.

*Evidence: **proven** = you ran it · **traced** = you read the whole chain (a source opened this
session counts) · **suspected** = neither.* Only proven and traced can carry a one-way door.

Five steps: **map, scope, candidates, deep dive, record**. Reviews stop after step 3, with no edits.
New/replaced parts use `references/design-new.md`; consequential forks only use `references/competing-designs.md`; settled small changes stay direct.

## 1. Map

Start from the project's map: `docs/architecture.md` (or the `architecture:` pointer in CLAUDE.md)
and recorded decisions (`docs/adr/`, `WHY.md`); a move that reopens a decision says why its reason
no longer holds. No map: sketch one from the entry points as you read, suggest `/project-foundation`
when available for next time, and go on. This design task does not depend on that skill. A map is a claim: check every edge you rely on against the code. A map
that says what the code does not do goes **first** in the report, with the line in each, because
every reader, human or AI, will believe a problem is solved that isn't.

## 2. Scope

Look where it hurts. Take the area or symptom the user named; otherwise the hotspots (recent
`git log`, files that change together, the tracker). Name the three changes most likely next and
where each came from: that is your yardstick for ranking. Follow the user-visible flows into the
scope from their entry points. Repo too big to read, or a history question: `references/instruments.md`.

## 3. Candidates

- **Consequential fork.** Set decision criteria before options; compare the simplest viable base with
  one structurally distinct alternative. Name costly stored/public contracts and say whether sketches
  were isolated/model-diverse or same-model fallback. See `references/competing-designs.md` for limits.
- **Chains and bottlenecks.** Follow one user action end to end. Something slow, fallible or not
  yours (network, email, an outside API) inside the user's wait is a lead; after a step you can't
  undo (a charge), its failure shows as an error after the damage. Count ripples: one change, N edits.
- **One owner per job.** Two API clients, three date helpers, config read five ways: count the copies.
- **Dependencies point one way**, toward the stable side. A cycle means its modules change together.
- **Logic apart from I/O.** Decision code that calls the network, database or clock can't run or be
  tested without them; inject at that edge. A port is earned only by what crosses a network or isn't
  yours; a dependency with a local stand-in (SQLite, a temp dir) gets none.
- **Small interface, a lot behind it.** Leads: a layer that only forwards, one concept chased
  across many tiny modules. **Clear boundaries**: one sentence per module, what it owns and must
  never know. **Data model first**: a wrong schema costs more than any code around it.
- **No structure nobody needs.** An interface with one implementer, a plugin system with one plugin,
  options nobody sets. One implementer is a guess, two is a fact (a test fake counts).
- **Hidden coupling.** Files in different modules that always change together with no import
  between them share an unnamed assumption; give it one owner.

**Deletion test**: undo it mentally; if complexity collapses, it's a finding. **Same-reason test**:
before merging, ask what would make each change; different answers mean separate jobs.

Don't flag what only looks bad: a module imported by many that imports nothing is a stable
foundation; a queue one flow skips may be one another flow needs. Before proposing to delete, merge
or inline, find why it exists (`git log -S`, or `code-history`) and every user, counting aliases
and string lookups. No proof it's dead, no deletion; proving it is `latent-audit`'s job, and
without it available, call it suspected.

**Reuse before you add.** When the better shape needs something (a table, a store, a queue, a
dependency), find who already owns that job, with `file:line`, and reuse it unless a requirement
rules it out. Name the second one you are *not* adding and what it would cost if wrong (a migration,
another thing to secure, back up and run). One format asked for is one function, not a plugin seam.

**Present**, answer first: the verdict (*clean / messy in places / tangled*) in one plain sentence
tied to the symptoms. Then 3–5 candidates, best first by cost counted × chance the change comes ÷
effort, each as a card (`references/visual-report.md`): the problem as the user feels it, the
chain behind it with `file:line` and a number, **before and after diagrams** (Mermaid, plain labels,
bottleneck marked), what gets cheaper or safer (counted), and a strength: *Strong*, *Worth
exploring* or *Speculative*. A move that makes nothing cheaper is tidying: drop it. Write the top
candidate out as a move: landing steps that each keep behavior unchanged, the **proof** (a command
showing it still works), and its door. Host can show a page: also build the HTML report, outside
the repo. A whole-codebase picture: `arch-map` if available, else draw Mermaid yourself.
Then **stop and ask which candidate to explore.** Change nothing yet.

## 4. Deep dive

Work the chosen candidate through with the user, one question at a time: constraints, the new
interface, what sits behind it, which tests survive. Ask the owner only what they can answer ("is
it fine if the receipt arrives a minute later?"); decide technical questions yourself and say so.

For an open design decision, give **two real options**, including the simplest viable one; compare
their forces. Then the **door**: a library or folder layout is two-way, decide
it in a line. A stored data shape, public API, datastore or auth model is one-way: check its facts
this session and give the user the options and the cost of being wrong first. Write dependencies
you'd use under ~10% of, or could write in ~100 lines, yourself; inline a seam with one caller and
under ~100 lines. Tests move to the new interface; the old parts' tests go. Re-count every number
before handing over. To build it, hand off to `build-discipline` or `evolve-maintain`.

## 5. Record

After the user decides or a move lands, update `docs/architecture.md` to match the code, in its own
format (small, as-is, every edge sourced); a stale map gets fixed here, with the user's OK. When the
user settles a one-way door, or rejects a move for a lasting reason, offer a short ADR
(`docs/adr/NNNN-<slug>.md`: context, decision, options rejected, consequences) so no later review
re-proposes it. A `docs/arch-design.md` handoff file only if asked (`references/instruments.md`).

*Test:* someone who can't read code can say what hurts, why, and what better looks like from your
pictures; every finding has a number or `file:line`; the top move has a second option, a door and a
proof; and you stopped to ask before changing anything.
