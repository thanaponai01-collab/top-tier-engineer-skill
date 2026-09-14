---
name: latent-audit
description: Sweep an existing codebase with no reported symptom for dead code, layer violations, and dormant bugs, and prove anything is dead before suggesting deletion. Use for "find dead code", "delete unused components", "check the layers are respected", "clean up the codebase".
---

# Latent Audit

**Code nothing appears to reference is not dead. It is suspected dead.** Nothing gets deleted until
it's proven nothing reaches it, because deleting live code is the one mistake a non-coder can
neither see coming nor diagnose afterwards.

## Rules

1. **Run the graph first.** The bundled script (in this skill's `scripts/` folder; stdlib Python,
   Python sources) measures the import graph:

   ```
   python <this skill's base directory>/scripts/graph-audit.py <src> [--layers layers.txt] [--entry module] [--json]
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
