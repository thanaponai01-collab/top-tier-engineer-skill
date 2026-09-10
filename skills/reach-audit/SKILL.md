---
name: reach-audit
description: >
  Read a whole system for what it exposes and what nothing ever reaches — every surface inventoried and marked served, orphaned, or unknown. Use for "what do we actually have / what do we serve / what did I build that nothing calls / what's never been used", or for a fast first read of an unfamiliar codebase. One named component is wire-check; proving an orphan safe to delete is latent-audit.
---

# Reach Audit

> **Asks:** What does this system serve, and what does nothing reach?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## Boundaries

one named component → `wire-check` (this skill runs its method over a whole system, and hands single-component questions back to it); proving an orphan is safe to delete → `latent-audit`; "is this code good/wise?" → `senior-review`; shape metrics → `structure-gate`; a felt complaint → `symptom-audit`; one gap and one move instead of an inventory → `toptier-lens`.

One principle, everything else serves it: **reach is a property of paths, not of reference counts.**
A thing with callers is not reached unless a path from a real entry point runs through one of them,
and a path is live only if every condition along it can actually hold. A declaration is not a path.
This is why an import graph cannot answer the question and why this skill exists next to
`latent-audit` rather than inside it: that skill measures **unreferenced** (no in-edge), this one
measures **unreached** (no live path). Neither list contains the other, and the one that matches
*"I built it and nothing uses it"* is this one.

## The method is `wire-check`'s

Borrowed, not restated (Law 1). Open `<root>/skills/wire-check/SKILL.md` and take three things from
it unchanged: **the Five Links** (Exists → Registered → Routed → Invoked → Reachable), **entry-point-first
tracing**, and **the reproduce ladder** — static trace, load probe, direct invocation, end-to-end
trigger — stopping at the cheapest rung this environment can actually execute. What differs here is
only the subject and the direction: `wire-check` has a destination and asks *does a path reach it?*
This skill has none and asks *what do all the paths reach, and what is left over?*

Read against something nothing reaches, that same table becomes a **classifier**. The first
unsatisfied link names what you have and who owns it next — which is why one pass is enough:

| First unsatisfied | What you actually have | Owner |
|---|---|---|
| 2 Registered | built; nothing in the system knows it exists | `latent-audit` (prove it dead) or `build-discipline` (wire it) |
| 3 Routed | discoverable, but no trigger maps to it | `build-discipline` |
| 4 Invoked | routed, but the condition on the path never holds | the **director** — a flag nobody sets, a branch nobody takes, a caller nobody calls is a decision, not a bug |
| 5 Reachable | it runs, and its effect lands nowhere | `debug-protocol` — a live defect wearing dead weight's costume |

Link 1 needs no row: anything the inventory found exists by construction.

## Operating contract

1. **The entry-point census is the ceiling.** Everything downstream inherits it, so it is done first
   and reported as a number, not assumed. Enumerate the *kinds* of way in — what can start work in
   this system: a request, a schedule, a message, a human at a terminal, another service, a build
   step — and derive each kind's instances from the code (`wire-check` Rule 2: this system's real
   mechanisms, never a remembered recipe). A missed entry point does not return a smaller answer, it
   returns a **wrong** one: every surface that entry point serves silently becomes an orphan, and an
   orphan list is what the director acts on.
2. **Enumerate twice, independently, then subtract.** Build the **inventory** — every unit a director
   would call a thing we built — from the source. Build the **served set** by walking forward from
   the census. Orphans are `inventory − served`. Deriving the inventory *from* the walk makes orphans
   unfindable by construction, which is how a sweep returns a confident, empty, worthless result.
3. **The unit is the surface, not the file, and you stop at the first unsatisfied link.** You never
   need all five failures; the first already names the owner. This bound is what makes a whole-system
   read cheap enough to run on a whim — and the line where this skill ends: one that reads every file
   has become `senior-review` and should say so and stop.
4. **Unreached is not unused.** Anything the walk cannot follow — dispatch by string name, reflection,
   a table built at runtime, a cron job, another service, a human running a script — is **UNKNOWN**,
   never an orphan. Per §8 it is reported as its own count and never folded into a clean result. This
   is `latent-audit`'s refusal to promote (suspected) to deleted, arriving one step earlier, and it is
   the rule this skill is most tempted to skip: an UNKNOWN column makes a report look less finished
   than a wrong one does.
5. **Classify; never condemn, never wire unasked.** Each orphan gets exactly one of three outcomes,
   and the third is a real answer, not a dodge: **wire it** (→ `build-discipline`), **drop it**
   (→ `latent-audit`, which owns the disconnection proof this skill deliberately does not attempt),
   or **accept it, with the reason written down** — a deferred feature, an API kept for callers
   outside the tree, a deliberate spike. Accepted orphans are recorded per §3 with their reason, so
   the next audit does not re-litigate them (§8: a known thing is frozen with its reason, not
   rediscovered). This skill deletes nothing and wires nothing itself.

## Procedure

1. **Census the ways in.** Rule 1. State the count and the kinds before reading anything else; where
   a kind exists but its instances can't be enumerated, that kind is UNKNOWN from the start and every
   later number is qualified by it. Executability census too (§1): an environment that cannot run the
   system caps every reach claim at **(trace-only)**, and the report's first lines say so.
2. **Inventory the surfaces.** Rule 2, from the source, in the director's units — not in modules.
3. **Walk and subtract.** Forward from each entry point along the reproduce ladder's cheapest
   executable rung. A surface reached under a condition is served only if that condition can hold
   (the principle above); if you can't tell, it is UNKNOWN, not served and not orphaned.
4. **Classify and route.** The classifier table, one line per orphan, first unsatisfied link only.
   Findings met on the way that aren't reach questions — a defect, a security shape, a judgment call
   — are recorded with `file:line` and an evidence tag and routed to their owner; this skill never
   expands into a full review.
5. **Report.** Inline; a file only when §3 warrants one. In the director's own questions, in their
   words, not in link names:
   - **What we have** — the inventory, one line each.
   - **What we serve** — the served set: what someone outside can actually cause to happen.
   - **What never reaches** — each orphan, its first unsatisfied link in plain words, its proposed outcome.
   - **What we couldn't settle** — the UNKNOWN set, and for each, the one command or fact that settles it.

## Verdict

One `REACH` line per `PROTOCOL.md` §5:

`findings(entries: E, surfaces: N, served: M, orphaned: K, unknown: U)` — the entry count leads
because Rule 1 makes it the ceiling of everything after it.

`clean(entries: E, surfaces: N, all served)` is claimable **only at `unknown: 0`**. Any UNKNOWN at
all means `findings`, even when every settled surface was served: a walk that could not follow half
the system has measured half a system, and calling that clean is the one lie this skill can tell.
`blocked(<what would unblock it>)` when no entry point could be established — with none, there is no
such thing as reach, and a guess here poisons every row.

## Failure modes this contract exists to prevent

An orphan list handed to the director as a delete list; "never used" pinned on the module a cron job
loads by string name; an inventory quietly derived from the walk that was supposed to test it; a
whole-system read that turned into an unrequested review; and the quiet one — a green `REACH: clean`
from a walk that never found the second way in.
