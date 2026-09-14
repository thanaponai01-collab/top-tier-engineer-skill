---
name: wire-check
description: Check that code is actually connected to the running system, not just written. Use when something "was built but isn't working", "is this hooked up?", after multi-file additions, or for "what do we actually serve / what did I build that nothing calls?" across a whole system.
---

# Wire Check

Code that exists is not code that runs. Generators are very good at writing components and very
unreliable at connecting them. This skill checks the whole chain, from where the system really
starts to where the component really has an effect, and when a link is broken, says why.

## Rules

1. **Trace from the entry point inward.** Start where the system starts (process launch, route
   table, event loop, CLI dispatcher) and walk towards the code. Tracing outward from the new code
   only shows what it *could* connect to, and misses the most common failure: a complete component
   nothing imports.
2. **Work the chain out from this codebase.** Find how *this* system registers components, routes
   requests and calls things by reading its code. Don't apply a remembered framework recipe.
3. **Every link is proven or traced.** If running it is cheap, traced is not a final answer.
4. **A broken link gets a cause, a fix, and a prevention.** Which link failed, why it was missed,
   the code that connects it, and the habit or check that stops it happening again.

## The five links

| # | Link | Holds when | Typical break |
|---|------|------------|---------------|
| 1 | **Exists** | The file is there, complete, loadable | Stub bodies, half-written files, syntax errors |
| 2 | **Registered** | Whatever finds components knows about it | Missing import/export, absent from manifest, config or container |
| 3 | **Routed** | Some external trigger maps to it | Route or handler never declared; name doesn't match convention |
| 4 | **Invoked** | Real execution reaches it with real arguments | Branch nothing takes, flag left off, wrong argument shape |
| 5 | **Reachable** | Its effect lands (response, DB, file, event) | Result discarded, error swallowed, wrong target |

Walk them in order. The first broken link is the finding; later links are *blocked*, not failed.

## Procedure

1. **Map.** Find the real entry points and how this system does each link. Build a small table:
   each component against where each of its five links should be declared.
2. **Walk.** For each link, use the cheapest evidence that settles it, stopping at the first step
   this environment can actually run:
   1. Read the connecting code end to end (traced).
   2. Load it: import, compile or boot the relevant part.
   3. Call it through the system, not by importing it directly (that skips the wiring under test).
   4. Fire the real trigger (request, CLI command, event) and watch the effect.
3. **Repair.** Ship the connecting code in the same response.

## Whole-system mode

When no single component is named ("what do we serve, what does nothing reach?"):

1. **Count the ways in first.** List every kind of entry (request, schedule, message, CLI, other
   service, build step) and its instances. A missed entry point turns everything it serves into a
   false orphan.
2. **Build two lists separately, then subtract.** An *inventory* of everything built, from the
   source. A *served set*, by walking forward from the entry points. Orphans = inventory − served.
   Building the inventory from the walk guarantees an empty, wrong answer.
3. **Unfollowable is unknown, not orphaned.** Calls by name in strings, dynamic lookups, cron jobs,
   external callers: mark UNKNOWN and count them separately. Never report "all served" while
   anything is unknown.
4. **Classify each orphan by its first broken link:** not registered (wire it, or prove it dead
   and delete it), not routed (wire it), never invoked (a flag or branch nobody takes: a decision
   for the owner), effect lost (a live bug that looks like dead weight). Delete nothing and connect
   nothing unasked.

## Report

- The first break, in plain words, and anything still only traced with the one command that would
  prove it.
- A table: component, links 1–5 as ✅ / ❌ / ⛔ blocked, proven / traced / suspected, the exact missing
  declaration. In whole-system mode: surface, served / orphaned / unknown, first broken link,
  proposed outcome.
- The connecting code.
- One recommendation: the check that stops this kind of gap coming back.

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.
