---
name: reach-audit
description: >
  Read a whole system for what it exposes and what nothing ever reaches — every surface inventoried and marked served, orphaned, or unknown. Use for "what do we actually have / what do we serve / what did I build that nothing calls / what's never been used", or for a fast first read of an unfamiliar codebase. One named component is wire-check; proving an orphan safe to delete is latent-audit.
---

# Reach Audit

> **The question:** What does this system serve, and what does nothing reach?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

one named component → `wire-check` (this skill runs its method over a whole system, and hands single-component questions back to it); proving an orphan is safe to delete → `latent-audit`; "is this code good/wise?" → `senior-review`; shape metrics → `structure-gate`; a felt complaint → `symptom-audit`; one gap and one move instead of an inventory → `toptier-lens`.

One principle, and everything else serves it: **being reached is about paths, not about how many
things point at it.** Something with callers is not reached unless a path from a real entry point
runs through one of them, and a path is live only if every condition along it can actually be true.
Declaring something is not a path to it. That is why an import graph cannot answer this question,
and why this skill sits next to `latent-audit` instead of inside it: that skill measures
**unreferenced** (nothing points at it), this one measures **unreached** (no live path runs to it).
Neither list contains the other, and the one that matches *"I built it and nothing uses it"* is
this one.

## The method is `wire-check`'s

Borrowed, not repeated (Law 1). Open `<root>/skills/wire-check/SKILL.md` and take three things from
it unchanged: **the Five Links** (Exists → Registered → Routed → Invoked → Reachable), **tracing
from the entry point first**, and **the ladder of ways to check** — static trace, load probe, call
it directly, trigger it end to end — stopping at the cheapest step this environment can actually
run. All that differs here is the subject and the direction: `wire-check` has a destination and
asks *does a path reach it?* This skill has no destination and asks *what do all the paths reach,
and what is left over?*

Applied to something nothing reaches, that same table becomes a way to **classify** it. The first
link that fails tells you what you have and who takes it next — which is why one pass is enough:

| First unsatisfied | What you actually have | Owner |
|---|---|---|
| 2 Registered | built; nothing in the system knows it exists | `latent-audit` (prove it dead) or `build-discipline` (wire it) |
| 3 Routed | discoverable, but no trigger maps to it | `build-discipline` |
| 4 Invoked | routed, but the condition on the path is never true | the **director** — a flag nobody sets, a branch nobody takes, a caller nobody calls is a decision, not a bug |
| 5 Reachable | it runs, and its effect goes nowhere | `debug-protocol` — this is a live bug that looks like dead weight |

Link 1 needs no row: anything the inventory found obviously exists.

## The job

1. **Counting the ways in sets the limit for everything else.** Everything after it depends on it,
   so do it first and report it as a number, never assume it. List the *kinds* of way in — what can
   start work in this system: a request, a schedule, a message, a person at a terminal, another
   service, a build step — and find each kind's actual instances in the code (`wire-check` Rule 2:
   this system's real mechanisms, never a recipe you remember). Missing an entry point does not
   give you a smaller answer, it gives you a **wrong** one: everything that entry point serves
   quietly turns into an orphan, and the orphan list is what the director acts on.
2. **Build two lists separately, then subtract.** Build the **inventory** — everything a director
   would call a thing we built — from the source. Build the **served set** by walking forward from
   the entry points. Orphans are `inventory − served`. If you build the inventory *from* the walk,
   no orphan can ever show up, which is how a sweep returns a confident, empty, useless result.
3. **Work in surfaces, not files, and stop at the first link that fails.** You never need all five
   failures; the first one already names the owner. That limit is what makes a whole-system read
   cheap enough to run on a whim — and it is where this skill ends: a pass that reads every file has
   turned into `senior-review`, and should say so and stop.
4. **Not reached is not the same as not used.** Anything the walk cannot follow — a call by name in
   a string, a dynamic lookup, a table built while running, a cron job, another service, a person
   running a script — is **UNKNOWN**, never an orphan. Per §8 it gets its own count and is never
   folded into a clean result. This is the same refusal `latent-audit` makes when it will not turn
   (suspected) into deleted, arriving one step earlier, and it is the rule this skill is most
   tempted to skip: an UNKNOWN column makes a report look less finished than a wrong one does.
5. **Classify; never condemn, never connect anything unasked.** Each orphan gets exactly one of
   three outcomes, and the third is a real answer, not a dodge: **connect it** (→
   `build-discipline`), **drop it** (→ `latent-audit`, which owns the proof that nothing reaches it —
   this skill deliberately does not attempt that), or **accept it, with the reason written down** —
   a feature put off, an API kept for callers outside this tree, a deliberate spike. Accepted
   orphans are recorded per §3 with their reason, so the next audit does not argue about them again
   (§8: something known is frozen with its reason, not rediscovered). This skill deletes nothing and
   connects nothing itself.

## Procedure

1. **Count the ways in.** Rule 1. State the count and the kinds before reading anything else. If a
   kind exists but you cannot list its instances, that kind is UNKNOWN from the start and every
   later number is qualified by it. Check what can be run here too (§1): an environment that cannot
   run the system caps every claim about reach at **(trace-only)**, and the report's first lines say
   so.
2. **Inventory the surfaces.** Rule 2, from the source, in the director's units — not in modules.
3. **Walk and subtract.** Forward from each entry point, using the cheapest step of the ladder this
   environment can actually run. Something reached only under a condition counts as served only if
   that condition can be true (the principle above); if you cannot tell, it is UNKNOWN — neither
   served nor orphaned.
4. **Classify and route.** Use the table above, one line per orphan, first failing link only.
   Anything you find on the way that is not a reach question — a bug, a security issue, a judgment
   call — is recorded with its `file:line` and an evidence tag and sent to whoever owns it; this
   skill never grows into a full review.
5. **Report.** Inline; a file only when §3 warrants one. In the director's own questions, in their
   words, not in link names:
   - **What we have** — the inventory, one line each.
   - **What we serve** — the served set: what someone outside can actually cause to happen.
   - **What never reaches** — each orphan, its first unsatisfied link in plain words, its proposed outcome.
   - **What we couldn't settle** — the UNKNOWN set, and for each, the one command or fact that settles it.

## Verdict

**Verdict noun:** `REACH`

One `REACH` line per `PROTOCOL.md` §5:

`findings(entries: E, surfaces: N, served: M, orphaned: K, unknown: U)` — the entry count leads
because Rule 1 makes it the ceiling of everything after it.

`clean(entries: E, surfaces: N, all served)` may be used **only at `unknown: 0`**. Any UNKNOWN at
all means `findings`, even if everything you could settle turned out to be served: a walk that
could not follow half the system has measured half a system, and calling that clean is the one lie
this skill can tell. Use `blocked(<what would unblock it>)` when no entry point could be
established — with none, reach means nothing, and a guess here ruins every row.

## Common mistakes

Handing the director an orphan list as if it were a delete list; calling a module "never used"
when a cron job loads it by name; quietly building the inventory from the same walk that was
supposed to test it; a whole-system read that turned into a review nobody asked for; and the quiet
one — a green `REACH: clean` from a walk that never found the second way in.
