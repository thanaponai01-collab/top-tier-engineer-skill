---
name: latent-audit
description: >-
  Find dead code and layer violations, proving code dead before deleting it. Use for "find dead code", "clean up the codebase", "are the layers respected?"
disable-model-invocation: true
metadata:
  stage: review
  card: "dead code and layer violations"
---

# Latent Audit

**Code nothing appears to reference is not dead. It is suspected dead.** Finding why it might still
run is your job: reading loaders, schedules and configs. Proving it is the helper's: nothing is
deleted until a deletion in a throwaway copy breaks nothing that could have noticed. `H` below is
`python <this skill's base directory>/scripts/graph-audit.py`.

## Steps

1. **Measure.** `H <repo> [--layers layers.txt]`. `MAPPED` files are named by the repo's
   `FEATURES.md` (`feature-map`) and are live. `DEAD MODULE CANDIDATES` and `UNUSED DEFS` are
   suspects only: imports by a built name (`import_module(f"...{x}")`, `getattr`, registries,
   schedules, config keys, CLI tables, cron, other services) never show in the graph.
2. **Find what could reach each suspect.** Search its name and name fragments (`rollup_daily` is
   `rollup-daily` in a schedule), read every loader, check outside callers. Write one line per
   suspect: `dead: <why nothing reaches it>` or `live: <what reaches it>`. Largest first, about 15
   in one run; say how many were left unchecked.
3. **Checkpoint before any deletion.**
   `H <repo> --try-delete <files> --run "<command that would reach them>" ...`
   It runs the map's recorded runs, VERIFY.md's checks (`verify-loop`), the unit tests and each
   `--run` in a copy, before and after deleting. Name with `--run` every command your step 2 found
   that could load the code (the job runner, each export format, the app's commands).

   | Verdict | Then |
   |---|---|
   | `breaks(...)` | Live. Keep it; the line names what broke |
   | `nothing-breaks(...)` | Delete it, unless step 2 found evidence of an outside caller (a cron line, a deploy config, another service naming it); a caller you can only imagine is not one |
   | `weak(tests only)` or `unchecked(...)` | Do not delete: add the `--run` commands it asks for, or list it as *watch* |

4. **Delete small.** One candidate per commit (the code, its dead tests, its dead config) so any
   mistake reverts in one step. Then, if the repo has a map, `python .features/features.py check
   --rerun`; if it has VERIFY.md, `verify.py status`. Report only, unless asked to delete.
5. **Layers, only against a written declaration.** The order comes from the project's architecture
   docs or the user, as a layers file (top layer first; a module may import the same or lower
   layers):

   ```
   interface: app/routes/, app/cli/
   domain:    app/services/
   data:      app/models/, app/db/
   ```

   No declaration: report "layers unchecked", never "clean", and never invent an order. A breach is
   a real import at a real line; fixing the code or the declaration is the owner's call.
6. **Note bugs you pass, don't chase them**: `file:line` and move on.

## Report

- **Removed**: each file with its `DELETE-CHECK` line and why nothing reaches it.
- **Kept, though it looked dead**: each file and what reaches it.
- **Watch**: suspects without a `nothing-breaks`, and how many were never checked.
- Layer breaches with the two remedies, then bugs noted along the way.

*Test:* every removed file has a `nothing-breaks` verdict whose checks include every command step 2
found that could reach it, or the app's own commands when step 2 found none. Code nothing loads is
dead: "no command ever loaded it" is the finding, not a reason to keep it.
