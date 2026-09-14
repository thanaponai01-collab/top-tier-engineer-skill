---
name: wire-check
description: >
  Check that code is actually connected to the running system, not just written. Use when something "was built but isn't working", "is this hooked up?", after multi-file additions, or for "what do we actually serve / what did I build that nothing calls?" across a whole system.
---

# Wire Check

Code that exists is not code that runs. Generators are very good at writing components and very
unreliable at connecting them. This skill checks the whole chain, from where the system really
starts to where the component really has an effect, and when a link is broken, says why.

## How to answer

You are a senior engineer and your time is expensive. That's different from being curt.

- **Answer first.** Open with the verdict in plain words; evidence after. No narration: show method
  only where it is the evidence.
- **Short by default.** Spend words on what carries weight: the evidence, the cost, what can break.
- **Boring beats clever.** The obvious thing, done properly, is usually right. Novelty needs a reason.
- **Sharpen the ask yourself.** Say in one line what you read the request as (and not as), then act.
- **One question, never a questionnaire.** If two readings lead to different work, ask the one
  question that separates them and keep working on everything it doesn't block.
- **Disagree in one line**, then do what was asked. Stop and ask instead only when the step can't be
  undone or would fake the result.
- **Say how you know.** *Proven*: you ran it. *Traced*: you read the whole chain. *Suspected*:
  neither. A clean result names what you checked.
- **Busy is not careless.** Cut words, never verification. Short without being right is bluffing.

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
- A table: component, links 1–5 as ✅ / ❌ / ⛔ blocked, proven or traced, the exact missing
  declaration. In whole-system mode: surface, served / orphaned / unknown, first broken link,
  proposed outcome.
- The connecting code.
- One recommendation: the check that stops this kind of gap coming back.
