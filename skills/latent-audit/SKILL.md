---
name: latent-audit
description: >
  Sweep an existing codebase with no reported symptom for dead code, layer violations, and dormant bugs, and prove anything is dead before suggesting deletion. Use for "find dead code", "delete unused components", "check the layers are respected", "clean up the codebase".
---

# Latent Audit

**Code nothing appears to reference is not dead. It is suspected dead.** Nothing gets deleted until
it's proven nothing reaches it, because deleting live code is the one mistake a non-coder can
neither see coming nor diagnose afterwards.

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

## Rules

1. **Run the graph first.** The bundled script (in this skill's `scripts/` folder; stdlib Python,
   Python sources) measures the import graph:

   ```
   python scripts/graph-audit.py <src> [--layers layers.txt] [--entry module] [--json]
   ```

   Its graph numbers are measurements. Its dead and unused lists are **suspects**, and the report
   says so in those words. For other languages, build the reference graph with the best available
   tooling and say how.
2. **Check layers against a written declaration, never taste.** Layer order comes from the project's
   architecture docs or the user, written as a layers file (top layer first; a module may import
   the same or lower layers only):

   ```
   interface: app/routes/, app/cli/
   domain:    app/services/
   data:      app/models/, app/db/
   ```

   No declaration → report "layers unchecked", never "clean", and never invent an order. A breach is
   a real import at a real line; whether to fix the code or change the declaration is the owner's
   call.
3. **Three checks before anything goes on the delete list:**
   1. Search every way it can be referenced: imports, names in strings, config keys, CLI and CI
      files, templates, dynamic lookups (`getattr`, `import_module`, route tables, plugin
      registries).
   2. Check outside callers: cron jobs, webhooks, other services, people running scripts.
   3. If the code can run here, run the tests or a tracer and confirm it never loads.

   All three pass → delete list. Any unfinished → *watch, don't delete*. There's no path from
   suspected to deleted.
4. **Deletions ship small and reversible.** One candidate per commit (the component, its dead tests,
   its dead config) with the proof attached, so any mistake reverts in one step.
5. **Record bugs you pass, don't chase them.** Leaked resources, unhandled errors, races, injectable
   string building: note `file:line` and move on. This is not a full review.

## Procedure

1. **Ground yourself.** Read project notes and recent history: a "dead" module may be deliberately
   postponed work. Check what can run here; with no runtime, deletion proofs stop at traced, and the
   report says so up front.
2. **Measure.** Run the script; write a layers file if the architecture declares layers.
3. **Prove or drop.** Run the three checks on every candidate.
4. **Trace breaches.** For each layer breach, read the import and say what it couples; give the two
   remedies (fix the code / change the declaration).

## Report

- How much of the codebase was swept, what's safe to delete, and what deleting it buys.
- One row per candidate: file or symbol, dead / unused / breach / watch, the proof or the unfinished
  check, proposed action.
- Script output, full deletion proofs, and bugs noted along the way after.

## Common mistakes

Deleting a module a cron job loads by name; removing plugin-registry targets because no import
mentions them; calling layers clean when none were declared; a 40-file cleanup commit nobody can
revert; handing over the script's suspect list as a safe-to-delete list.
