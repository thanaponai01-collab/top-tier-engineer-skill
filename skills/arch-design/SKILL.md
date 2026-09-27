---
name: arch-design
description: Improve a codebase's structure, or shape a new one, judged by what the next likely change costs. Measures duplicated systems, misdrawn boundaries, hidden coupling and over-building from the code and its git history, decides with options and reversibility, and ends in one file — docs/arch-design.md — whose moves are written out buildable. Use for "where can the architecture improve?", "is my codebase bloated?", "why does every change touch six files?", restructuring, module or API boundaries, choosing a stack or pattern, or greenfield architecture.
---

# Architecture & Design

Architecture is the cost of the next change. Good structure lands a likely change in one place; bad
structure scatters it across many, or pays up front for a change that never comes. Everything below
measures that cost from the code and its history, not from taste. Design for a maintainer you'll
never meet, often an AI: the structure must be navigable from the files alone.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to end, or
opened the source (docs, lockfile, a fetch) this session · **suspected** = neither. Only *proven* and
*traced* can carry a one-way door.*

One loop, whether the code exists or not: **Aim → Measure → Diagnose → Decide → Move → Verify.** With
code, the *as-is* comes from the repo. Greenfield, it's empty, and the likely changes come from the
requirements.

## 1. Aim

Write down two things before reading further:
- **The question**, in one line: "the order flow: why does adding one field touch six files?"
- **The yardstick:** the three changes most likely to come next, and where you got them (the user,
  the requirements, the issue tracker, the last month of `git log`). Every later judgment is one
  question: does this make those changes cheaper?

Read only what those changes reach, from the entry points inward. Sweep the whole repo only when the
user asked about the whole repo. Greenfield: get the requirements (ask, or state the ones you're
assuming); a structural claim with no requirement behind it is *speculative*.

*Test:* you can name the three changes, where they came from, and what you deliberately did not read.

## 2. Measure

Three instruments, and the history is the one people skip. The code shows what is *connected*; only
the history shows what *changes together*.

- **Concept map.** Where each concept lives: users, auth, config, data access, outside calls,
  errors, and the domain's own nouns. One table, `concept | owner(s) | file:line`, kept in your
  working notes, not filed. Start from `FEATURES.md` `trace:` lines if they exist (`feature-map`),
  else trace the entry points as `explain` does; never write a separate map doc. A row with two
  owners is a lead.
- **Change history.** `python <this skill's base directory>/scripts/change-map.py <repo> [--depth 2]`
  reports spread (modules touched per commit), hidden coupling (file pairs in *different* modules
  that keep changing in the same commit) and hotspots (churn × size). Exclude what is coupled on
  purpose, such as a version file and its changelog, with `--exclude`. Script not available → read
  `git log -n 50 --name-only` by hand and count the same three things. No history at all →
  greenfield rules: the rehearsal below is your only measure.
- **Rehearsal.** Walk each yardstick change through the map: which files do you edit? Count the
  modules. More than two for one change means a boundary is drawn in the wrong place.

Budget: two passes of Measure and Diagnose. If a third seems needed, the yardstick is too wide or
too vague; go back to Aim and narrow it, or report what you have and stop.

*Test:* every lead you carry forward has a `file:line` or a number from the history behind it.

## 3. Diagnose

A lead becomes a finding by passing two tests:

- **Deletion test.** Undo it in your head: merge the duplicates, inline the layer, drop the
  interface. If the complexity collapses into something smaller, it's a finding. If it just moves
  somewhere else, it isn't.
- **Same-reason test**, before any merge. Ask what would make each of the two change. The same
  answer means one owner. Different answers mean they only look alike, and merging them drags each
  along with the other's changes. A display date and a tax-filing date can be byte-identical today
  and still change for different reasons.

What the findings look like:
- **One job, many owners:** two API clients, three date helpers, config read five ways.
- **Shotgun change:** one concept smeared so that each change touches many modules. High spread,
  or a failed rehearsal.
- **Hidden coupling:** files that change together with no import between them. A format, schema or
  assumption is shared and has no named owner. Give it one.
- **Built for "gonna need":** an interface with one implementation, a plugin system with one
  plugin, options nobody sets, a layer that only passes calls through. Count today's callers.
- **The place everything lands:** a top hotspot that every feature edits.
- **Wrong direction:** a lower layer that knows about a higher one, or domain code that names a
  technology. `latent-audit`'s graph proves layer breaches; without it available, read the imports
  and label the finding *traced*.
- **Half-built or unreachable:** it stays *suspected* here. Proving it dead is `latent-audit`'s job;
  with that not available, it stays *suspected* in the report and you propose no deletion.

**Badge each finding.** **Strong** means the cost is counted today (copies, call sites, co-change
count). **Worth exploring** means the payoff depends on the yardstick changes actually coming.
**Speculative** means the deletion test was ambiguous. If every finding is Speculative, the verdict
is *clean*: say so rather than dressing a clean result up as a list. If the project keeps a decision
log, read it first. A finding that restates a settled decision isn't new, and one that contradicts
a settled decision names the entry it contradicts. Before a finding proposes merging, inlining or
deleting something, ask `code-history` why it exists (one question, aimed at that file or symbol):
a recorded reason is a force in the Decide step, and "no recorded reason" keeps the finding
*suspected*. Without `code-history`, read `git log -S` on the symbol yourself.

*Test:* every Strong finding has a number next to it.

## 4. Decide

Every structural choice goes through one frame: a greenfield boundary, a stack, or a finding whose fix
could take more than one shape.

1. **Two real options**, one of them the simplest thing that meets every requirement. Adopt it, or
   name the requirement that rules it out.
2. **Forces:** which requirements push which way.
3. **Door.** Two-way (a library, a folder layout, code behind an internal boundary): decide it and
   note it in one line. One-way (stored data shape, a public API, a datastore, the tenancy or auth
   model, deleting data): check every fact it rests on *this session* (fetch the vendor docs or
   pricing, read the lockfile, run it), then take the options, a recommendation and the cost of
   being wrong to the user *before* it becomes a move. No one to ask (an unattended run): leave the
   row out of the file, since `check` rejects an unconfirmed one-way door, and name it in the answer
   as "parked, needs a yes: <options, recommendation, cost of being wrong>".
4. **Bars.** A new dependency: under ~10% of it used, or under ~100 lines to write yourself, means
   you write it. For a one-way door, look up its health and license, don't recall them. A new layer
   or seam of your own: count its callers today and name the requirement that pays for it. One
   caller and under ~100 lines means you inline it.

Greenfield shapes as **boundaries and contracts, not technologies**: each module gets one sentence
of responsibility, what it owns, and what it must never know. Contracts say the data shape, the
error shape, and who may call whom. Each concept has exactly one owner. Then stress the design. Run
a pre-mortem ("a year on, this failed: the three likeliest reasons") and give each reason a design
change or an accepted risk. Name the element that protects each invariant.

*Test:* each decision row has a second option, a door, and an evidence label, and no one-way row
rests on memory.

## 5. Move

Moves, not a rewrite. Each one lands alone with its behavior proven unchanged, so each is a
reversible step. A rewrite is its own decision, raised with the user. Moves go last in the file,
one `## Move N: <title>` block each, in landing order, under the header's `context:` bullet that
states what every move assumes ("the auth model stays; the database doesn't change"). A move that
contradicts the context is a new decision, not a move.

```
## Move 1: <what changes, in one line>
- cost: <what it costs today, counted>
- pays: <which yardstick change gets cheaper: "add a report field: 6 files → 2">
- files: <paths, with the line numbers the evidence sits on>
- owner: <the one place that owns this job afterwards>
- callers: <every call site that has to change>
- door: <two-way, land it and go | one-way, confirmed: what the user said>
- proof: <the command to run, and the output that counts as success>
- effort: <S / M / L>
- after: <the move that must land first, or "nothing">
```

A move with no `pays:` line isn't improving the architecture. It's tidying, so drop it or say so. A
move with no `proof:` or no `door:` answer is not written as a move: ask it in the chat. Once the
moves land, the architecture's own proof is to re-run the rehearsal (and `change-map.py` after a few
weeks of commits): the yardstick changes should touch fewer modules.

*Test:* someone who never saw this run could build from the block alone. If they'd need to open the
report, read the code or ask you something, a field is missing. Fill it now, while the code is in
front of you.

## 6. Verify

Every number above was produced by the same run that's now vouching for it; re-reading your own
notes confirms them, it doesn't test them. For each Strong finding and each move, re-derive it
instead: rerun `change-map.py` against the co-change counts cited, grep the repo for every name in a
`callers:` list, re-walk the `pays:` rehearsal by hand, re-open the `code-history` source. A number
that doesn't reproduce loses its badge or gets fixed.

That's cheap self-checking, not a second opinion. For each Strong finding and one-way door, also
delegate per PHILOSOPHY §8: a fresh subagent, told the fact to verify ("count the current callers of
`orders.legacy_client`") but never the conclusion ("...so it's safe to inline") — a prompt that leaks
the answer only invites agreement. A disagreement fixes the finding or drops its badge, noted in
`evidence:` ("subagent recounted: 3 callers, not 1"). Skip it for Worth-exploring and Speculative
findings; they already carry their own hedge.

*Test:* every Strong finding and one-way door was re-derived by a tool this session, and checked by
a subagent that was never told the expected answer.

## Deliver

Answer first. For an audit, that's the verdict (*clean / messy in places / tangled*) and the one move
that pays the most. For a design, it's the structure in plain words and the decision that's most
expensive to reverse.

**Size it to the question.** A single decision that leaves nothing to build is answered in the chat
as its decision row, with no file. Anything more gets **one file**, built for the agent that reads
it next: `key: value` bullets, one block per finding, decision and move, no prose beyond the verdict.

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

## Move 1: <title>       (the block from §5, one per move, in landing order)
```

Put the assumption every move shares ("the auth model stays") in one `context:` bullet in the header.
Moves stay last. Diagrams, before-and-after tables and the concept map are not part of the file;
they are a human's aid (below).

**Check it.** `python <this skill's base directory>/scripts/arch-design.py check <file>` fails on a
missing field, a file or line that is not in the repo, a one-way door with no `confirmed:` (or resting
on a *suspected* fact), a strong finding with no number, and an `after:` that names no move. It
reports `STALE` when a file the moves name changed after `at:`. Fix what it says before you hand the
file over; a file that fails its own check is not buildable. Script not available: check those by hand.

**Path.** If the user named a path, use it. Otherwise `docs/arch-design.md` for the whole system, and
`docs/arch-design-<topic>.md` for one area. A rerun on the same topic overwrites the file; git holds
the earlier versions. Set `status: landed` once the moves are in; from then the repo, not this file,
is the source.

**Decisions that outlive the moves.** A one-way decision belongs in the project's decision log, if
it keeps one: append the row there too. This file goes stale once the moves land; the log does not.

**A picture, whenever there are moves.** Verdict *clean* or a single decision row: no picture. Otherwise
hand `arch-map` the Change view, the evidence and the headline; it writes its own file, and you link
it in `diagram:`. Give it each move's number for the box or arrow it changes, and a table already
written, `move | what | cost | effort`, copied from the Move blocks. Marks: added `+`, removed `-`,
changed `~`, problems `!N`, with a legend. The reader approves moves by number from that picture, so a
box with no move number on it is a gap. If `arch-map` isn't available, draw Mermaid yourself.

*Test:* the run ends with a path you can name and a `check` that exits 0. What happens to the moves
after that — filed as issues, handed to a build loop, read by a person — is the next skill's
decision, not this one's; the file is written to stand alone either way.
