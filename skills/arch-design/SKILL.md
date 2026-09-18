---
name: arch-design
description: Shape a system's structure, or audit an existing codebase for duplicated systems, over-building and AI slop. Use for greenfield architecture, choosing a stack or pattern, module or API boundaries, restructuring, "how should this be structured / which stack?", or "is my codebase bloated / where can the architecture improve?".
---

# Architecture & Design

You deliver a structure that can be read back and undone, not diagrams. Every choice that matters
is made in the open: the options, what pushed each way, and how hard it is to reverse. Design for a
maintainer you'll never meet, often an AI: the structure must be navigable from the files alone.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end, or opened the source (docs, lockfile, a fetch) this session · **suspected** = neither. Only
*proven* and *traced* can carry a one-way door.*

Pick the mode:
- **Design:** nothing is built yet, or a new part is about to be.
- **Audit:** it's already built. Find where the structure went wrong and the moves that fix the most.

## Design mode

### 1. Inherit
Read the requirements (ask for them, or state the ones you're assuming). Every structural claim
traces to a requirement or is flagged as speculative. If code exists, map its real structure from
the entry points inward before proposing anything.
*Test:* each structural claim has a requirement beside it, or the word *speculative*.

### 2. Shape
Define the system as **boundaries and contracts**, not technologies:
- Modules, each with a one-sentence responsibility, what it owns, and what it must never know.
- Contracts between modules: data shape, error shape, who may call whom.
- Conventions stated once and then followed; errors structured and machine-parseable.

**One of each.** Every concept (users, auth, config, a data source, a job queue) has one owner that
everything else calls. Before adding a module, store, service or pipeline, find the one that already
does this job and extend it. Two systems doing one job means two places to fix, secure, scale and
keep in sync; one means one place to cache, index and speed up. But merge only what changes for the
same reason: two things that merely look alike today stay separate, or they drag each other along.

*Test:* someone could replace any one module by reading only its contract. If not, the boundary is
wrong — fix it before going on.

### 3. Decide
Every consequential choice goes through this frame:

1. **At least two real options**, one of which is the **simplest thing that meets every
   requirement**. Adopt it, or name the requirement that rules it out.
2. **Forces:** which requirements and constraints push which way.
3. **Reversibility.** Two-way door (a library, a folder layout): decide fast, note briefly.
   One-way door (database, public API shape, tenancy model, auth model): ground it first (next
   item), then the options, a recommendation and the cost of being wrong go to the user before you
   walk through it.
4. **Dependency bar.** A new dependency needs: rough cost to write the needed part yourself, the
   fraction of the library you'd use, maintenance health (recent releases, open security issues),
   license compatibility, and a pin plan. Default: under ~10% used, or under ~100 lines to write →
   write it. For a one-way door, "maintenance health" and "license compatibility" are looked up this
   session (the registry page, the repo's release list), not recalled.
5. **Complexity bar.** A new layer, registry or plugin seam of your own needs the callers it has
   **today** (counted) and the requirement that pays for it. One caller and under ~100 lines →
   inline it. Run the deletion test too: imagine it gone — does the complexity it hides reappear
   across those callers, or does nothing reappear because there was nothing there yet to hide?
   Nothing reappearing is the same answer as one caller: inline it.
6. **Say how you know — and for a one-way door, know it from this session.** A two-way door can run
   on a remembered claim; fix it fast if it's wrong. A one-way door can't, so its claims get checked
   *before* the recommendation is written, not cited from memory and labeled after the fact: fetch
   the vendor docs, current pricing or a benchmark (`WebFetch`/`WebSearch`), or read the lockfile,
   config or a run for a version or behavior claim. "Postgres handles our write volume (fetched
   vendor docs, 2026-09; not benchmarked)" is *traced* and earns the recommendation; "Postgres
   handles our write volume (vendor docs)" with no fetch behind it this session is *suspected* —
   say so plainly, and either look it up or hand the user the gap before recommending, don't dress
   an assumption up as a citation.

*Test:* every decision row names a second option, the simplest one is either adopted or refused by a
named requirement, and every fact behind a one-way-door row traces to something you opened or ran in
this session — not remembered. A row with one option, or a one-way-door fact with no session behind
it, is not a decision yet.

### 4. Stress
- **Pre-mortem:** "A year later this failed. Name the three likeliest reasons." Each gets a design
  change or an accepted risk.
- **Requirement walk:** point to the structural element that guarantees each invariant. One with
  no owner is unprotected.
- **Duplicate count:** list each capability and how many places do it. More than one → merge them,
  or write down why they must stay apart.
- **Change rehearsal:** narrate the two likeliest future changes. Touching more than two modules
  means the boundaries are misdrawn.
- **Novelty check:** rejecting a common pattern or using an unusual one needs a recorded reason —
  check the decision log first for one already on record before writing a new one.

*Test:* every pre-mortem reason has a design change or a written accepted risk next to it, and
every invariant names the element that protects it.

### 5. Deliver
The material, in this order: the structure in plain words and the decision most expensive to
reverse; before → after diagrams (greenfield has no *before*, draw *after* only); the module table
(responsibility / owns / must not know); contracts; conventions; requirement → structure mapping;
and `decision | options considered | forces | reversibility | evidence`.

If the project keeps a decision log, append new entries; replacing a decision adds an entry rather
than deleting the old one.

## Audit mode

Codebases built fast grow the same system twice and build for futures that never came. Find it,
prove it, rank the fixes.

**Scope it first.** Name the area and the question in one line ("the order flow — why does adding
one field touch six files?"), then map only what the entry points into that area reach. A whole-repo
sweep is for when the user asked about the whole repo; anywhere else it is reading you paid for and
won't use.
*Test:* you can name what you deliberately did not read, and why it can't affect the answer.

1. **Map what's really there.** From the entry points inward: each module, what it actually does,
   and where each concept lives (users, auth, config, data access, outside API calls, errors). One
   table. If the project keeps a decision log, read it now — a finding that only restates a decision
   already settled there isn't a new finding.
2. **Hunt the slop.** Each sign is a finding only with `file:line` evidence, and only if it passes
   the deletion test: undo it in your head — merge the duplicates, delete the pass-through, drop the
   interface — does the complexity concentrate somewhere smaller, or does it just move? Only
   "concentrates" earns a finding.
   - **Same job, many places:** two API clients, three date helpers, config read five ways, the
     same query pasted into every handler.
   - **Built for "gonna need":** an interface with one implementation, a plugin system with one
     plugin, options nobody sets, a layer that only passes calls through.
   - **One place doing everything:** the file every feature lands in; a function that fetches,
     decides and renders.
   - **Half-built or unreachable:** features started and left, code nothing calls. Report it as
     *suspected* and hand the proof to `latent-audit`; nothing is called dead here. No
     `latent-audit` available → it stays *suspected* in the report and you propose no deletion.
   - **Noise:** handling for cases that can't happen, errors swallowed silently, comments that
     restate the code.
   - **No shared way:** the same problem solved differently in each part.

   *Test:* every finding names a `file:line` you opened. A sign you recognised but didn't locate is
   not a finding yet.
3. **Badge each finding, then rank by badge.** The deletion test result from step 2 is the badge:
   - **Strong** — the complexity reappeared clearly, and its cost today is counted (call sites,
     copies, `file:line`), not felt.
   - **Worth exploring** — the complexity reappeared, but the payoff rides on where the code goes
     next rather than on what it costs today.
   - **Speculative** — the deletion test was ambiguous, or the cost is unmeasured. Surfaced for
     completeness; most of these are safe to leave alone.

   Rank by badge, then by cost within a badge. A report where every finding is Speculative is the
   verdict *clean* wearing a list — say clean.
   *Test:* every Strong finding has a counted cost next to it. A badge with no number behind it is
   Worth exploring at best.
4. **Prescribe moves, not a rewrite.** Each move: what merges or goes, the one owner left behind,
   every caller that changes, and the check that proves behavior didn't (tests green before and
   after). Moves land one at a time. A rewrite is its own decision, raised with the user.

   **Gate the one-way doors.** A move that deletes data, changes a public API shape, or merges an
   auth or tenancy model is a one-way door wearing a move's clothing. It goes through Decide's
   reversibility rule — options, a recommendation, the cost of being wrong — to the user before the
   block is written, not after. A move that only touches code behind a boundary nothing outside the
   codebase depends on is a two-way door: decide it and write the block.

   **Check it against what's settled.** A move that only re-proposes something the decision log
   already rejected isn't a move — drop it. One that contradicts a settled decision but the friction
   is real enough to reopen it still gets written up, with the entry it contradicts named plainly,
   not silently overridden.

   *Test:* before merging two things, you can say what would make each of them change. Same answer
   → merge. Different answers → they only look alike, and they stay apart. And for every move you can
   name which door it is — a move with no answer to that is not ready to be written.

The material, in this order: the plain verdict (clean / messy in places / tangled) and the one move
that pays most; *before*, the concept map as it is with each finding's number (`!1`, `!2`) on the box
where it lives; *after*, the same map with the moves applied; then
`# | sign | where | what it costs today | move | effort | badge`.

## The moves — the last section, one block per move

The audit's moves, and the design's modules to create, are the build's work. They go last, under a
`## Moves` heading, in the order they land. A block is not a summary of a move; it is the whole move:

```
### 1. <what changes, in one line>
cost:     <what it costs today — the reason this is worth doing at all>
files:    <paths, with the line numbers the evidence sits on>
owner:    <the one place that owns this job afterwards>
callers:  <every call site that has to change>
door:     <two-way — land it and go | one-way — confirmed with the user, what they said>
proof:    <the command to run, and the output that counts as success>
effort:   <S / M / L>
after:    <the move that must land first, or "nothing">
```

Above the blocks, one short **Context** paragraph: what every move assumes (the auth model stays,
the database doesn't change). A move that contradicts it is a new decision, not a move.

*Test — self-containment:* could someone who never saw this audit build from this block alone? If
they would have to open the report, read the code, or ask you a question, a field is missing. Fill
it now, with the code still in front of you; this is the only moment that context is free.

A move whose proof line you can't name is not a move, and neither is one whose door you can't name
— both stay in the report as a question, not a block.

Filing these as tracked issues is `issue-handoff`'s job, from the file alone, whenever the user
wants them. Never ask about it mid-audit; you finish at the file.

## The file

**Size it to the question first.** A single decision that leaves nothing to build — one library,
one boundary, which of two shapes — is answered in the chat as its decision row: options, forces,
reversibility, evidence, and no file. There is a file when the work has more than one module,
more than one finding, or a move someone builds from later — and it is one file, because a moves
file living beside the report drifts from it at the first edit of either.

When there is a file, hand the finished material to `arch-map` in one go — the **Change** view, the
path, everything under **Deliver**, and the move blocks to go last under `## Moves`. Name the path
after what this run is about, not the skill that wrote it: `docs/arch-design-<topic>.md`, with the
bare `docs/arch-design.md` only for the one run that covers the whole system with nothing narrower
to name.

**Every run gets its own file — never overwrite a prior run's.** Before naming the path, list `docs/`
for that base name. If it's free, use it bare. If it's taken (by this run's own earlier draft in the
same session, or by a run from before), count the existing `<base>.md`, `<base>-2.md`, `<base>-3.md`
… and use the next number — `docs/arch-design-checkout-flow.md`, then `-2.md`, then `-3.md`, and the
same numbering for the bare `docs/arch-design.md` fallback. This applies even when the topic is
identical to a previous run: a second pass over the same area is a new file, not an edit of the old
one, so both stay readable and the old one isn't silently rewritten. Unless the user named a path —
then that exact path, always, overwritten on rerun like any file they point you at. `arch-map` owns
the notation, the legend and how the file lands, and it will ask for whatever is missing; what it
asks for is work you still owe.

**No `arch-map` available here — a different agent, or only this file copied out — then you write
the file yourself**, at that path, in the Deliver order above, with the moves last. Diagrams go in
as Mermaid in a fenced block; mark added `+`, removed `−`, changed `~`, problems `!N`, and give the
legend for the marks you used.
*Test:* the run ends with a path you can name. Announcing a handoff and finishing with no file is
the failure this paragraph exists to stop.

## Common mistakes

Diagrams with no decisions behind them; "decisions" with one option; walking through a one-way
door without stopping, including inside a move block; a second system built for a job the first
already does; two things merged because they looked alike, not because they change together; a
finding badged Strong with no counted cost behind it; re-proposing a move the decision log already
rejected, unread; announcing the handoff to `arch-map` and leaving no file anywhere; technology
names in boundary descriptions, which stop being true the moment the stack changes; reusing a prior
run's file path without checking `docs/` first, silently overwriting the earlier report instead of
landing on the next numbered name; citing "vendor docs" or "benchmarks" for a one-way door without
having fetched them this session — a remembered claim wearing a citation's clothes, and the exact gap
the *suspected* label exists to catch.
