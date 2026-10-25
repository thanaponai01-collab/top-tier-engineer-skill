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

**Goal:** remove the code nothing reaches, keep everything that is reached, and account for every
file that looked dead. How you find what reaches it is yours. What counts as done is checked by
the helper. `H` is `python <this skill's base directory>/scripts/graph-audit.py <repo>`.

Run `H --gate` whenever you like; it says which stage is open and what fixes it, and prints the
answer once all three hold (`LATENT-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Snapshot** | Before anything changes, `H --snapshot --run "<cmd>" ...` ran every command that could load code and recorded what each one imported (the map's recorded runs, VERIFY.md and the unit tests are added for you). Every runtime loader the helper finds (`import_module(f"...")`) loaded at least one of its suspects, or `.latent/verdicts.md` says `- loader <file:line>: <why it loads none>` |
| **2. Change** | Only files the snapshot never saw loaded are deleted, in place, and every snapshot command still passes. A deleted file whose name another file spells (a schedule, a config) needs `- <file>: dead: <why that line never loads it>` |
| **3. Account** | Every suspect still here that the snapshot never loaded has a line in `.latent/verdicts.md`: `dead` (report without deleting), `watch` (keep, with why), or `live` (with the `file:line` that loads it) |

`H --gate --run "<cmd>" ...` takes the snapshot and checks the stages in one call.

## Other tools

- `H` alone: the import graph. Files `FEATURES.md` (`feature-map`) names are `MAPPED` and live.
- `H --try-delete <file> ... --run "<cmd>"`: for code a snapshot cannot observe (it loads outside
  Python, or its entry point cannot run here). Deletes in a throwaway copy and reruns everything;
  a `nothing-breaks` receipt lets stage 2 accept a deletion the snapshot did not cover.
- `H --layers layers.txt`: imports that point up a declared layer order (top first, e.g.
  `interface: app/routes/`). No declared order means "layers unchecked", never "clean".

Report only, unless asked to delete. Commit `.latent/` with the change.
