---
name: build-discipline
description: Build in small, proven, fully-wired increments. Use when writing or generating code for a feature, tool or system, or resuming a half-finished build. Trigger on "build it", "implement this", "add the feature", "make it work".
---

# Build Discipline

You never leave code nothing calls. Work moves in **slices**: the smallest piece that can be proven
working end to end. A slice isn't done until it's connected, run, and committed in a state the
system could ship from. Only a result you actually ran closes a slice.

## Starting from a brief

When a design, an audit or a ticket already worked the change out (`gh issue view 12`, a spec,
`docs/arch-moves.md`), each entry is a slice: take its proof line as your own and start at **Build**. Re-deriving
it from the report or the code is the same thinking paid for twice. Two checks first: the proof line
runs from a real entry point, and the files it names still look the way the brief says — a brief
written before the last three commits is a claim, not a fact. A vague proof line gets sharpened out
loud, never quietly swapped for an easier one.

## Per slice: Plan → Build → Wire → Prove → Commit

### 1. Plan
- Pick the smallest change that produces observable behavior reachable from the real entry point.
  "Half a backend with no caller" is not a slice; "one endpoint, wired, returning real data for one
  case" is.
- Write the **proof line** before coding: the exact command or interaction that shows it works, and
  what output counts as success. Can't state it? The slice is too vague.

### 2. Build
- **Smallest change that satisfies the proof line.** Delete or reuse before adding.
- **Simple first, then let measurements pay for more.** A known limit becomes a written note with a
  measured trigger (`p95 > 300 ms at 10k rows`), not structure built on fear.
- **Check where the change lands.** Smallest-change is measured against the slice, not the file.
  Adding to an already-overloaded file is the easiest move every time, and fifty easy moves make a
  file nobody can test. If the target file is already too big, pull out the seam this slice needs
  first (a behavior-preserving move you can prove), then add the behavior.
- **Error paths first:** bad input, missing dependency, partial failure, before polishing the happy
  path.
- **Names explain.** A function whose name doesn't explain it gets renamed before it gets a comment.
- **No new conventions mid-slice.** If existing conventions don't cover a case, stop and decide it
  explicitly.
- **Deferred work needs a trigger.** `what | why | trigger that makes it due`. Prefer a trigger a
  machine checks (an assert, a test). A deferral without a trigger is a wish.

### 3. Wire
Trace everything the slice added through five links, starting from the real entry point:
**Exists → Registered → Routed → Invoked → Reachable** (effect actually lands). Code nothing can
reach means the slice failed.

### 4. Prove
- Run the proof line. Paste the actual output. A described result doesn't close the slice.
- Exercise at least one error path the slice claims to handle.
- If execution is impossible here (no runtime, missing credentials), say so **in bold at the top**
  and record "prove in first environment that can run it" as deferred work.

### 5. Commit
- **Read the whole diff as if reviewing someone else's code.** Every line must be one you can
  explain and meant to make.
- One slice, one commit. The message states the behavior change and the proof result.
- Reverting this commit alone must return the system to its previous working state.

## Resuming an interrupted build

Before writing anything: read open deferrals, the last slice's proof line, and `git log` / the
uncommitted diff. Re-run the last claimed-working proof before stacking on it. A result from a
changed codebase is no longer proven.

## Rules

- No slice starts while the previous one is unproven.
- Never fix a failing proof by weakening the proof line. Fix the code, or raise it if the
  requirement itself looks wrong.
- Generated code meets the same bar as handwritten code.

## Report

What now runs that didn't before, and what was deferred. A table: slice, proof line, proven or
traced, what the user can now do. Diffs and proof output after.

## Common mistakes

Building everything and proving it at the end; modules waiting for a caller that never arrives;
happy-path-only code; TODO comments nobody returns to; unrevertable commits; "it should work" as a
claim of done; fifty proven slices appended to one overloaded file.
