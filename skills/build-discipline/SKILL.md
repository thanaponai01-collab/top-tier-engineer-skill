---
name: build-discipline
description: >-
  Build features in small, proven slices, wired from entry point to effect.
metadata:
  stage: build
  card: "build a multi-file feature in proven slices"
---

# Build Discipline

You never leave code nothing calls. Work moves in **slices**: the smallest piece that can be proven
working end to end. A slice is done when a check you ran passes, the code is connected to a real
entry point, and it is committed in a state the system could ship from. A described result closes
nothing.

## Where the build lives

For context discovery, current-work scaling and completion upkeep, follow
[the context handoff](../project-setup/references/context-handoff.md), preserving existing equivalents.

A build outlives one sitting, so keep one file, `BUILD.md` at the repo root (or the brief's own file
if it has one). One line per slice: `proof line | status | commit`. Under it, a **Deferred** list:
`what | why | trigger that makes it due`, the trigger a check a machine can run (an assert, a test,
`p95 > 300 ms at 10k rows`); a deferral without one is a wish. Keep the next slice under a
`## Next` heading, one or two lines, so a fresh session finds it without reading the log. Read it
first every session, with the `## Decisions` in `BRIEF.md` and linked areas relevant to the slice;
update it in the same commit as the slice. RUN.json, when present, owns execution state; keep
`## Next` consistent with it rather than maintaining a competing task order.

**What the owner wants lives in `BRIEF.md`, not in the chat.** When the owner states or changes a
decision mid-build, even in passing, record it there before the slice that acts on it: replace the
line it overrides and move the old one to `BRIEF.archive.md` (`problem-framing`, "Keeping the brief
current"). No `BRIEF.md` yet: create one with the job in a line and a `## Decisions` section. Then
check the project's agent instruction file (`CLAUDE.md`, `AGENTS.md`) has a start-here block linking
`BRIEF.md` and `BUILD.md`; add one if not (`project-setup`, "Make it discoverable"). A decision
honoured in the code but written nowhere is lost the next time a session starts.

`BUILD.md` is a log of every slice ever proven, so it grows for the life of the project unless
something takes lines back out. Once it passes about 40 slice lines, archive the ones that are
`proven`, committed, and whose feature has stayed green since (check `FEATURES.md` /
`VERIFY.md` if the repo has them): move them verbatim to `BUILD.archive.md`. Keep at most five
milestone summaries linking archived ranges and current feature checks in `BUILD.md`; merge older
summaries as history grows. Individual proof lines and commits stay in the archive, so startup
reading stays bounded independently of the number of completed slices. Never archive a slice
that is `traced` but not `proven`, uncommitted, or still on the Deferred list: those are exactly
what the next session needs in full. Do the archive pass in the same commit that would otherwise
push the file over the line, not as a separate cleanup.

## Starting from a brief

When a design, audit or ticket already worked the change out (`gh issue view 12`, a spec, the
`## Moves` section of `docs/arch-design.md`), each entry is a slice: take its proof line as yours and
start at **Build**. Two checks first: the proof line runs from a real entry point, and the files it
names still look the way the brief says. A brief older than the last few commits is a claim, not a
fact. A vague proof line gets sharpened out loud, never quietly swapped for an easier one.

## Per slice: Aim â†’ Build â†’ Connect â†’ Prove â†’ Commit

### 1. Aim
- Pick the smallest change with observable behavior reachable from the real entry point. "Half a
  backend with no caller" is not a slice; "one endpoint, wired, returning real data for one case"
  is.
- Write the **proof line** before any code: a command the loop can run itself, and the output that
  counts as success. Better still, a test that fails now. Can't state it? The slice is too vague.
- Set a budget: if the slice needs more than about three attempts or touches more than it should,
  split it. Don't grind. A slice that cannot be split smaller and is still failing: stop, and report
  what you know, what failed and what you would try next.

*Test:* the proof line is in `BUILD.md` before the first edit, as a command plus expected output.

When the project has VERIFY.md or the task asks for reusable verification, hand the slice's
requirement-backed check, entry point and adjacent regressions to `verify-loop`: load that skill,
follow its references/handoff.md and record the rejection and strict green through its bundled
`verify.py`. Direct output files are the fallback only when verify-loop is not installed. Do this
before the product change. The wrong state is the missing behavior. BUILD.md keeps the proof/status
entry and evidence location, even for one slice; VERIFY.md owns the check definitions.

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
  Several slices, some for other agents? `plan-work` marks which can run together and how to merge
  them back; without it, hand out only slices that touch different files and share no function.

### 3. Connect
Trace what the slice added from the real entry point through five links:
**Exists â†’ Registered â†’ Routed â†’ Invoked â†’ Reachable** (the effect actually lands). Code nothing can
reach means the slice failed.

*Test:* for each link you can say what you did to check it, not that you believe it holds.

*Evidence labels: **proven** = you ran it Â· **traced** = you read the whole chain, start to
end Â· **suspected** = neither.*

### 4. Prove
- Run the proof line and keep the real output. Exercise at least one error path the slice claims to
  handle.
- Never fix a failing proof by weakening it. Fix the code, or raise it if the requirement looks
  wrong.
- For a reusable recipe, run verify-loop after each slice and finish with `run --strict`, then
  current green `status`. If no behavioral rejection was retained, challenge a spec-backed product
  mistake in scratch copies and finish strict verification again. Changed check definitions need
  fresh proof and a new baseline under verify-loop's rules; a prose fail-proof note is insufficient.
  Keep prior mapped behavior green and report unmapped coverage. New features may use a completed
  check before implementation or a controlled mutation afterwards; never weaken expectations.
- If verify-loop is unavailable, use native checks and retain real negative/passing outputs.
  Report the missing strict evidence explicitly. Ordinary slices without a reusable recipe still
  use their direct proof line; no mandatory setup or skill chain is introduced.
- If nothing here can run it (no runtime, missing credentials), say so **in bold at the top** and add
  "prove in the first environment that can run it" to Deferred.

*Test:* the report contains output you pasted, not a sentence describing output.

### 5. Commit
- Read the whole diff as if reviewing someone else's code. Every line must be one you meant to make.
- One slice, one commit; the message states the behavior change and the proof result. Reverting it
  alone returns the system to its previous working state. Commit when the person or the calling
  skill (`drive`, `drive-overnight`) has said to; otherwise leave the slice staged, say so, and
  record the slice in `BUILD.md` as uncommitted.

*Test:* you can name one line you changed your mind about, or say plainly that the whole diff
survived the read. Nothing reconsidered usually means it was skimmed.

## Resuming an interrupted build

Read `BUILD.md`, `git log` and the uncommitted diff. Re-run the last slice marked proven before
stacking on it: a result from a changed codebase is no longer proven. No slice starts while the
previous one is unproven.

## Report

What now runs that didn't before, and what was deferred. A table: slice, proof line, proven or
traced, what the user can now do. Diffs and proof output after.
Before reporting completion, confirm BUILD.md contains this slice's command, result and commit
or uncommitted status, alongside current verification evidence when a reusable recipe is used, and
that every decision the owner stated this session is in `BRIEF.md` or a linked current area, with nothing left there
contradicting it, and that the agent instruction file's start-here block links `BRIEF.md`. Say in
the report where each one was written.

Project memory: retrieve missing facts with `project-context`; after authorized changes use
`project-update` for affected records. Without helpers, follow/update existing notes directly;
read-only reviews report gaps. Skip upkeep when no durable fact changed.
