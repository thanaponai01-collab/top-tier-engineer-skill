---
name: arch-design
description: Improve a codebase's structure, or shape a new one, judged by what the next likely change costs. Measures import cycles, duplicated systems, hubs, pass-through layers, seams, hidden coupling and over-building from the code, its import graph and its git history, decides with options and reversibility, and ends in one file — docs/arch-design.md — whose moves are written out buildable. Use for "where can the architecture improve?", "is my codebase bloated?", "why does every change touch six files?", restructuring, module or API boundaries, choosing a stack or pattern, or greenfield architecture.
---

# Architecture & Design

Architecture is the cost of the next change. Good structure lands a likely change in one place; bad
structure scatters it across many, or pays up front for a change that never comes. Everything below
measures that cost from the code and its history, not from taste. Design for a maintainer you'll
never meet, often an AI: the structure must be navigable from the files alone.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to end, or
opened the source (docs, lockfile, a fetch) this session · **suspected** = neither. Only *proven* and
*traced* can carry a one-way door.*

One loop, whether the code exists or not: **See → Judge → Shape.** With code, the *as-is* comes from
the repo. Greenfield, it's empty, and the likely changes come from the requirements.

## 1. See

Write down two things first:
- **The question**, in one line: "the order flow: why does adding one field touch six files?"
- **The yardstick:** the three changes most likely to come next, and where each came from (the last
  month of `git log`, the issue tracker, the user, the requirements). Every later judgment is one
  question: does this make those changes cheaper?

Read only what those changes reach, from the entry points inward; sweep the whole repo only when
asked about the whole repo. Greenfield: get the requirements, or state the ones you're assuming; a
structural claim with no requirement behind it is *speculative*.

Then run the instruments. The code shows what is *connected*; only the history shows what *changes
together*; a rehearsal shows what one change *costs*.

- **Import graph** (Python). `latent-audit` owns the graph: `python <latent-audit base>/scripts/graph-audit.py
  <src> --edges edges.json`, then `python <this skill's base directory>/scripts/dep-map.py edges.json`.
  It lists import cycles (with file:line), the most-imported modules and how unstable each is,
  modules that only forward their arguments, Protocol/ABC seams with how many classes implement
  each, and modules that import a network, database or process library. These are leads, not
  verdicts. Either script not available, or not Python: grep the imports of the modules the
  yardstick reaches, and label what you find *traced*.
- **Change history.** `python <this skill's base directory>/scripts/change-map.py <repo> --json > change.json`
  reports spread (modules touched per commit), hidden coupling (file pairs in *different* modules
  that keep changing in the same commit) and hotspots (churn × size). Exclude what is coupled on
  purpose (a version file and its changelog) with `--exclude`. Then
  `dep-map.py edges.json --cochange change.json` says which coupled pairs have *no import edge*
  between them: a shared format or assumption nobody named. No history: the rehearsal is your only
  measure.
- **Rehearsal.** Walk each yardstick change through the code: which files do you edit? Count the
  modules. More than two for one change means something is drawn in the wrong place.
- **Concept map**, in your working notes, never filed: `concept | owner(s) | file:line` for users,
  auth, config, data access, outside calls, errors and the domain's own nouns. A row with two owners
  is a lead. Start from `FEATURES.md` `trace:` lines if they exist, else trace the entry points.

Budget: two passes of See and Judge. A third means the yardstick is too wide; narrow it, or report
what you have and stop.

*Test:* every lead you carry forward has a `file:line` or a number behind it, and you can name what you
deliberately did not read.

## 2. Judge

A lead becomes a finding by passing two tests:

- **Deletion test.** Undo it in your head: merge the duplicates, inline the layer, drop the
  interface. If the complexity collapses into something smaller, it's a finding; if it just moves
  somewhere else, it isn't.
- **Same-reason test**, before any merge. Ask what would make each of the two change. The same answer
  means one owner; different answers mean they only look alike, and merging drags each along with
  the other's changes. A display date and a tax-filing date can be byte-identical today.

What findings look like, and what to count:
- **One job, many owners:** two API clients, three date helpers, config read five ways. Count the copies.
- **Shotgun change:** one concept smeared across modules. Count the modules from the rehearsal.
- **Hidden coupling:** files that change together with no import between them. Give the shared
  format or assumption one named owner.
- **A cycle:** modules that import each other change together whatever their names say. Count the
  modules and pick the one edge that can point the other way.
- **Effects in the core:** domain code that calls the network, a database, the clock or a global
  itself cannot run or be tested without them. The missing piece is an injected dependency at that
  edge. Ask of every module the yardstick reaches: can it run with nothing outside the process?
- **Built for "gonna need":** an interface with one implementation, a plugin system with one plugin,
  options nobody sets, a layer that only forwards calls. A seam with one implementer is a guess, with
  two a fact (count them; the test fake counts). Count today's callers.
- **The place everything lands:** a top hotspot that every feature edits.
- **Half-built or unreachable:** it stays *suspected* here. Proving it dead is `latent-audit`'s job;
  without it available, propose no deletion.

**Do not flag what only looks bad.** A module imported by many that imports nothing is a stable
foundation; only one that is both widely imported and imports a lot makes changes ripple. A seam with
two real implementers earns its place.

**Badge each finding.** **Strong**: the cost is counted today. **Worth exploring**: the payoff
depends on the yardstick changes actually coming. **Speculative**: the deletion test was ambiguous.
If every finding is Speculative the verdict is *clean*; say so rather than dressing it up. If the
project keeps a decision log, read it first: a finding that restates a settled decision isn't new,
and one that contradicts it names the entry. Before proposing to merge, inline or delete something,
ask `code-history` why it exists (one question, aimed at that file or symbol); a recorded reason is
a force in Shape, and "no recorded reason" keeps the finding *suspected*. Without it available,
read `git log -S` on the symbol yourself.

**Rank** by cost counted × the chance the yardstick change comes ÷ effort. The top of the list is
the headline move.

*Test:* every Strong finding has a number next to it.

## 3. Shape

**Reuse before you add.** When the work asks for something new (a table, a store, a module, a format,
a dependency), first find who already owns that job in this repo: `file:line`, from the concept
map. Reuse that owner unless a requirement rules it out, and say what adding a second one would
cost if it turned out wrong: a migration, another thing to secure, back up and run. Design for the
cases asked for, not the ones you can imagine: one format is one function, not a plugin seam.

Every structural choice, whether a greenfield boundary, a stack, where new data lives or a finding
that could be fixed more than one way, goes through one frame:

1. **Two real options**, one of them the simplest thing that meets every requirement (often the
   existing owner). Adopt it, or name the requirement that rules it out.
2. **Forces:** which requirements push which way.
3. **Door.** Two-way (a library, a folder layout, code behind an internal boundary): decide it in one
   line. One-way (stored data shape, a public API, a datastore, the tenancy or auth model, deleting
   data): check every fact it rests on *this session* (fetch the vendor docs, read the lockfile, run
   it), then give the user the options, a recommendation and the cost of being wrong *before* it
   becomes a move. Nobody to ask: leave the row out of the file (`check` rejects an unconfirmed
   one-way door) and name it in the answer as "parked, needs a yes".
4. **Bars.** A dependency you would use under ~10% of, or could write in ~100 lines, you write. A
   new seam needs two implementers today or a named requirement that pays for it; one caller and
   under ~100 lines, you inline it.

The shape a move heads toward, in one line each: a module has a small interface and does a lot behind
it; each concept has one owner; dependencies point toward the stable side; logic that decides sits
apart from code that touches the outside world, and reaches it through an injected dependency; a
seam is a place two things really vary. How to test across a seam depends on what is on the other
side: in-process, merge and test directly; something with a local stand-in (an in-memory database),
test with it; your own service across a network, a port with a real and an in-memory adapter; a
third party, a port with a fake. Once a move's target interface is chosen, that is module design, not
architecture: shape it there, then come back here for the proof.

Greenfield shapes as boundaries and contracts, not technologies: each module gets one sentence of
responsibility, what it owns, what it must never know; contracts say the data shape, the error shape
and who may call whom. Then run a pre-mortem ("a year on, this failed: the three likeliest reasons")
and give each reason a design change or an accepted risk.

**Moves, not a rewrite.** Each lands alone with behavior proven unchanged. A rewrite is its own
decision, raised with the user. Moves go last in the file, one block each, in landing order, under a
header `context:` bullet that states what every move assumes ("the auth model stays"). A move that
contradicts the context is a new decision.

```
## Move 1: <what changes, in one line>
- cost: <what it costs today, counted>
- pays: <which yardstick change gets cheaper: "add a report field: 6 files → 2">
- files: <paths, with the line numbers the evidence sits on>
- owner: <the one place that owns this job afterwards>
- callers: <every call site that has to change>
- door: <two-way, land it and go | one-way, confirmed: what the user said>
- proof: <the command to run, the output that counts as success, and which old tests it replaces>
- effort: <S / M / L>
- after: <the move that must land first, or "nothing">
```

A move with no `pays:` line is tidying: drop it or say so. A move with no `proof:` or `door:` answer
is asked in the chat, not written. Once the moves land, the architecture's own proof is to repeat
the rehearsal (and `change-map.py` after a few weeks of commits): the yardstick changes should touch
fewer modules.

**Re-derive before you hand over.** Every number was produced by the run that vouches for it, so
recount it: grep every name in a `callers:` list, rerun `change-map.py` against the co-change counts
cited, re-walk the `pays:` rehearsal. A number that doesn't reproduce loses its badge. For each
one-way door, also give a fresh subagent the fact to verify ("count the current callers of
`orders.legacy_client`") and never the conclusion ("...so it's safe to inline"); a disagreement
fixes the finding, noted in `evidence:`.

*Test:* someone who never saw this run could build from a Move block alone, each decision has a
second option and a door, and no one-way row rests on memory.

## Deliver

Answer first. For an audit, the verdict (*clean / messy in places / tangled*) and the one move that
pays the most; for a design, the structure in plain words and the decision that's most expensive to
reverse. A single decision that leaves nothing to build is answered in the chat as its decision
row, with no file. Anything more gets **one file**, built for the agent that reads it next:
`key: value` bullets, one block per finding, decision and move, no prose beyond the verdict.

```
# ARCH-DESIGN
- at: <short sha the analysis was true of>
- question: <one line>
- yardstick: <change>; <change>; <change>   (each with how many modules it touches now)
- status: open | landed
- verdict: clean | messy in places | tangled
- diagram: <path>          (optional, only when arch-map drew one)

## Finding 1: <title>
- where: <file:line>
- cost: <counted today>
- badge: strong | worth exploring | speculative
- evidence: proven | traced | suspected, then how

## Decision 1: <title>
- options: <A> | <B>
- forces: <which requirements push which way>
- door: two-way | one-way, confirmed: <what the user said>
- evidence: proven | traced | suspected, then how

## Move 1: <title>       (the block from Shape, one per move, in landing order)
```

Put the assumption every move shares in one `context:` bullet in the header; moves stay last.

**Check it.** `python <this skill's base directory>/scripts/arch-design.py check <file>` fails on a
missing field, a file or line that is not in the repo, a one-way door with no `confirmed:` (or resting
on a *suspected* fact), a strong finding with no number, and an `after:` that names no move. It
reports `STALE` when a file the moves name changed after `at:`. Fix what it says before handing
over; a file that fails its own check is not buildable. Script not available: check those by hand.

**Path.** The user's path if named, else `docs/arch-design.md` for the whole system and
`docs/arch-design-<topic>.md` for one area. A rerun on the same topic overwrites it; git holds the
old one. Set `status: landed` once the moves are in. A one-way decision also belongs in the
project's decision log, if it keeps one: this file goes stale, the log does not.

**A picture, when there are moves.** Verdict *clean* or a single decision row: no picture. Otherwise
hand `arch-map` the Change view, the evidence, the headline, each move's number for the box or
arrow it changes, and the `move | what | cost | effort` table copied from the Move blocks; it writes
its own file, which you link in `diagram:`. A box with no move number on it is a gap. If `arch-map`
isn't available, draw Mermaid yourself or skip the picture.

*Test:* the run ends with a path you can name and a `check` that exits 0. What happens to the moves
after that (filed as issues, handed to a build loop, read by a person) is the next skill's decision;
the file is written to stand alone either way.
