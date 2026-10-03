---
name: arch-design
description: Improve, redesign or design a backend's structure. Looks at the code (or the requirements, if there is none), finds what is worth improving, says whether to patch a part or replace it, and gives simple, ordered moves using sound engineering technique. Use for "how can we improve this codebase / architecture?", "is my backend bloated?", "why does every change touch six files?", module or API boundaries, restructuring, "should we rewrite this part?", choosing a stack or pattern, or designing a new backend.
---

# Architecture & Design

Take a backend from where it is to a simpler, better-organized place, or design a new one that
starts there. Prefer the smallest structure that does the job. Design for a maintainer you'll never
meet, often an AI: the structure must be navigable from the files alone.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to end, or
opened the source this session · **suspected** = neither. Only *proven* and *traced* can carry a
one-way door.*

## 1. Pick the outcome

Say which one you chose and why; the user can override it.
- **Improve**: the structure is basically sound and the problems are local. Make targeted moves.
- **Replace a part**: one area's foundation is wrong (its data model, or a core everything bends
  around) and patching would cost more than rebuilding that part. Design the replacement and a way to
  move over behind a stable interface, one part at a time. Never propose replacing the whole system
  unless asked. Ask the user before recommending any replacement.
- **Design new**: no code yet, or a new system or module. Get the requirements, or state what you
  assume; a structural choice with no requirement behind it is *speculative*.

## 2. Look

Read from the entry points inward and trace the main flows; only the parts the question reaches.
Name the three changes most likely to come next and where each came from (recent `git log`, the
tracker, the user, the requirements): that is your yardstick, and it breaks ties when ranking. Repo
too big to read, or a question about history: see `references/instruments.md`.

## 3. Judge

Check what you read against these techniques. Each is a lead until it passes the two tests below.
- **One owner per job.** Two API clients, three date helpers, config read five ways: count the copies.
- **Dependencies point one way**, toward the stable side. A cycle means its modules change together.
- **Logic apart from I/O.** Decision code that calls the network, database or clock itself can't run
  or be tested without them; inject the dependency at that edge.
- **Small interface, a lot behind it.** A layer that only forwards calls, or a module whose
  interface is as large as its body, is a lead.
- **Clear boundaries.** Each module has one sentence of responsibility: what it owns, what it must
  never know.
- **Data model first.** A wrong schema or contract costs more than any code around it.
- **No structure nobody needs.** An interface with one implementer, a plugin system with one plugin,
  options nobody sets. One implementer is a guess, two is a fact (a test fake counts).
- **Hidden coupling.** Files in different modules that always change together with no import
  between them share an assumption nobody named; give it one owner.
- **Consistent errors, config and logging**, and seams you can test across.

Two tests turn a lead into a finding:
- **Deletion test.** Undo it in your head: merge the duplicates, inline the layer, drop the
  interface. If the complexity collapses, it's a finding; if it just moves, it isn't.
- **Same-reason test**, before any merge. Ask what would make each of the two change. The same
  answer means one owner; different answers mean they only look alike. A display date and a tax
  date can be byte-identical today.

Don't flag what only looks bad: a module imported by many that imports nothing is a stable
foundation. Put a number or a `file:line` next to every finding. Before proposing to delete, merge
or inline something, find out why it exists (`git log -S` on the symbol, or `code-history` if
available); a recorded reason is a force, and no proof it's dead means propose no deletion. Proving
code dead is `latent-audit`'s job; without it available, call it suspected.

## 4. Shape

**Reuse before you add.** When the work needs something new (a table, a store, a module, a
dependency), find who already owns that job, with `file:line`. Reuse it unless a requirement rules
it out, and say what a second one would cost if wrong: a migration, another thing to secure, back up
and run. Build for the cases asked for: one format is one function, not a plugin seam.

For every structural choice, give **two real options**, one being the simplest thing that meets
every requirement (often the existing owner), and the forces that push each way. Then the **door**:
a library or folder layout is two-way, decide it in a line. A stored data shape, public API,
datastore or auth model is one-way: check its facts this session, and give the user the options and
the cost of being wrong before it becomes a move. Write dependencies you'd use under ~10% of, or
could write in ~100 lines, yourself; inline a seam with one caller and under ~100 lines.

Design new: give module boundaries and contracts, not technologies: each module's one-sentence
responsibility, its data and error shapes, who may call whom. Then a pre-mortem ("a year on this
failed: the three likeliest reasons") with a design change or accepted risk for each.

## 5. Recommend

Answer first: the verdict (*clean / messy in places / tangled*) and the one move that pays most.
Then a ranked list, best first. Each move states:
- **what's wrong** (`file:line`, counted) and the **better shape**, tagged improve or replace
- **steps** in landing order, each landing alone with behavior unchanged
- **proof**: the command that shows it still works, and what should get cheaper ("add a report
  field: 6 files → 2")

Rank by cost counted × chance the change comes ÷ effort. A move that makes nothing cheaper is
tidying: drop it or say so. Re-count every number before handing over. If every finding is
speculative, the verdict is *clean*; say so. A file only if asked (format in the reference file);
for a picture, hand the moves to `arch-map`, or draw Mermaid if it isn't available.

*Test:* every finding has a number or `file:line`, each recommendation has a second option, a door
and a proof, and a stranger could start the first move from your answer alone.
