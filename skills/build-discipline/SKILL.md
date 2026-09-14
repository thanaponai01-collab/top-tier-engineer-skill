---
name: build-discipline
description: >
  Build in small, proven, fully-wired increments. Use when writing or generating code for a feature, tool or system, or resuming a half-finished build. Trigger on "build it", "implement this", "add the feature", "make it work".
---

# Build Discipline

You never leave code nothing calls. Work moves in **slices**: the smallest piece that can be proven
working end to end. A slice isn't done until it's connected, run, and committed in a state the
system could ship from. Only a result you actually ran closes a slice.

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

## Per slice: Plan → Build → Wire → Prove → Commit

### 1. Plan
- Pick the smallest change that produces observable behavior reachable from the real entry point.
  "Half a backend with no caller" is not a slice; "one endpoint, wired, returning real data for one
  case" is.
- Write the **proof line** before coding: the exact command or interaction that shows it works, and
  what output counts as success. Can't state it? The slice is too vague.

### 2. Build
- **Smallest change that satisfies the proof line.** Delete or reuse before adding. Add an
  abstraction on its second real use, not its first guess.
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
