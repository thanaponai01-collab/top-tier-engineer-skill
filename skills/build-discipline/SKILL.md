---
name: build-discipline
description: Build in small, proven, fully-wired increments. Use when writing or generating code for a feature, tool or system, or resuming a half-finished build. Trigger on "build it", "implement this", "add the feature", "make it work".
---

# Build Discipline

You never leave code nothing calls. Work moves in **slices**: the smallest piece that can be proven
working end to end. A slice is done when a check you ran passes, the code is connected to a real
entry point, and it is committed in a state the system could ship from. A described result closes
nothing.

## Where the build lives

A build outlives one sitting, so keep one file, `BUILD.md` at the repo root (or the brief's own file
if it has one). One line per slice: `proof line | status | commit`. Under it, a **Deferred** list:
`what | why | trigger that makes it due`, the trigger a check a machine can run (an assert, a test,
`p95 > 300 ms at 10k rows`); a deferral without one is a wish. Read it first every session; update
it in the same commit as the slice.

## Starting from a brief

When a design, audit or ticket already worked the change out (`gh issue view 12`, a spec, the
`## Moves` section of `docs/arch-design.md`), each entry is a slice: take its proof line as yours and
start at **Build**. Two checks first: the proof line runs from a real entry point, and the files it
names still look the way the brief says. A brief older than the last few commits is a claim, not a
fact. A vague proof line gets sharpened out loud, never quietly swapped for an easier one.

## Per slice: Aim → Build → Connect → Prove → Commit

### 1. Aim
- Pick the smallest change with observable behavior reachable from the real entry point. "Half a
  backend with no caller" is not a slice; "one endpoint, wired, returning real data for one case"
  is.
- Write the **proof line** before any code: a command the loop can run itself, and the output that
  counts as success. Better still, a test that fails now. Can't state it? The slice is too vague.
- Set a budget: if the slice needs more than about three attempts or touches more than it should,
  split it. Don't grind.

*Test:* the proof line is in `BUILD.md` before the first edit, as a command plus expected output.

### 2. Build
- **Smallest change that moves the proof line.** Delete or reuse before adding. Simple first; a known
  limit becomes a Deferred entry, not structure built on fear.
- **Check where the change lands.** Adding to an overloaded file is the easiest move every time, and
  fifty easy moves make a file nobody can test. If the target is already too big, first move out the
  seam this slice needs (behavior-preserving, provable), then add the behavior.
- **Error paths before polish:** bad input, missing dependency, partial failure.
- **Names explain.** Rename before commenting. No new conventions mid-slice; if the existing ones
  don't cover a case, decide it explicitly.
- **Delegating a slice?** The brief carries the proof line, the files it may touch, and what it must
  not. Its report is a claim: rerun the proof line yourself before marking the slice done.

### 3. Connect
Trace what the slice added from the real entry point through five links:
**Exists → Registered → Routed → Invoked → Reachable** (the effect actually lands). Code nothing can
reach means the slice failed.

*Test:* for each link you can say what you did to check it, not that you believe it holds.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

### 4. Prove
- Run the proof line and keep the real output. Exercise at least one error path the slice claims to
  handle.
- Never fix a failing proof by weakening it. Fix the code, or raise it if the requirement looks
  wrong.
- If nothing here can run it (no runtime, missing credentials), say so **in bold at the top** and add
  "prove in the first environment that can run it" to Deferred.

*Test:* the report contains output you pasted, not a sentence describing output.

### 5. Commit
- Read the whole diff as if reviewing someone else's code. Every line must be one you meant to make.
- One slice, one commit; the message states the behavior change and the proof result. Reverting it
  alone returns the system to its previous working state.

*Test:* you can name one line you changed your mind about, or say plainly that the whole diff
survived the read. Nothing reconsidered usually means it was skimmed.

## Resuming an interrupted build

Read `BUILD.md`, `git log` and the uncommitted diff. Re-run the last slice marked proven before
stacking on it: a result from a changed codebase is no longer proven. No slice starts while the
previous one is unproven.

## Report

What now runs that didn't before, and what was deferred. A table: slice, proof line, proven or
traced, what the user can now do. Diffs and proof output after.
