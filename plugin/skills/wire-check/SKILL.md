---
name: wire-check
description: >-
  Check that code is connected to the running system, not just written. Use for "built but isn't working", "is this hooked up?", "what does nothing call?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "built, but nothing happens"
---

# Wire Check

**Goal:** every component in question is either reached by a real way into the system or has its
first broken link named, and anything you connect stays connected after you leave. How you find the
links is yours: read it all if it fits, then run the real triggers. What counts as done is checked by
the helper. `W` is `python <this skill's base directory>/scripts/wire.py <repo>`.

`W` alone lists the ways in the repo declares and the code it picks by a name built at runtime.
Run `W --gate` whenever you like; it says which stage is open and what fixes it, and prints the
answer once they hold (`WIRE-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Snapshot** | `W --snapshot --run "<cmd>" ...` ran every way in (each CLI command, the job runner, each by-name variant, with the environment a deployment sets) in a throwaway copy, recording which functions each one entered. It is current with the code, and every declared way in was started, or `.wire/verdicts.md` says `- entry <name>: not run: <why>` |
| **2. Account** | Every function no command entered has a line in `.wire/verdicts.md` (the gate drafts the slots; a whole file takes one line): `not-registered`, `not-routed`, `never-invoked`, `effect-lost`, `unknown` (say what it depends on), or `served` by a way in that cannot run here. All but `not-registered` and `unknown` cite the `file:line` they rest on. A function a command should reach gets that command, not a verdict |
| **3. Keep** | Only for what you connected (`--target <file>::<function>`): a snapshot command enters it now; a `FEATURES.md` feature (`feature-map`) traces to its file and is proven; a `VERIFY.md` section (`verify-loop`) with that file in `path:` fires the real trigger, was seen red with the wiring broken and is green now |

`W --gate --run "<cmd>" ... --target <file>::<function>` takes the snapshot and checks the stages in
one call. A snapshot taken after the code changed keeps the first one as the before picture, so the
answer can say the target was never entered before the change.

Report only, unless asked to connect. Commit `.wire/`, `FEATURES.md`, `.features/` and `VERIFY.md`
with the change.
