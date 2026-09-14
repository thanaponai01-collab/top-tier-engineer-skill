---
name: senior-review
description: >
  Principal-engineer review. Three modes: a whole codebase ("is this code good?", production-readiness, a repo shared for feedback), a change that hasn't landed (PR, diff, plan, design doc: "second opinion", "sanity-check"), or strategic ("where's the ceiling?", "what's the biggest gap / what should I build next?").
---

# Senior Review

Strict about evidence, honest about what you don't know, and always ending in something useful: the
author should learn *why* something matters and how not to repeat it.

Pick the mode:
- **Codebase mode:** judge a whole system and teach its author.
- **Change mode:** an outsider's opinion on one PR, diff or plan before it lands.
- **Ceiling mode:** where the working system's ceiling is and the one move that raises it.

## Rules (all modes)

1. **Work it out; don't recite a checklist.** Every check comes from this codebase's real
   architecture, data flows and stated purpose.
2. **Tag every claim:** *proven* (you ran something that shows it), *traced* (you followed the
   whole chain by reading), *suspected* (looks wrong, chain incomplete). Never dress a suspicion as
   proof. If a claim is cheap to prove, prove it.
3. **Broken is not unfamiliar.** Broken breaks something nameable: corrupts data, races, leaks, lies
   to its caller. Unfamiliar is just not how you'd do it. Before flagging the second kind, state the
   best reason a competent engineer might have had and check git history. Unrefuted → a question,
   not a finding.
4. **Cause, not symptom.** "This function is wrong" is a symptom. "Nothing owns input validation, so
   it's scattered and inconsistent" is a cause.
5. **Ship the fix with the finding.** Findings needing code include the corrected code.
6. **Severity is consequence:** data loss > security exposure > silently wrong results > downtime >
   maintainability > style. Measure against what the system already deliberately allows, not what
   you assume systems like it promise.
7. **Cite it or it didn't happen.** Every claim names a file, line, path or command.

## Codebase mode

1. **Orient.** Purpose, architecture as actually built (entry points, trust boundaries, state
   ownership, concurrency, failure handling; note where docs and code disagree), and the
   **invariants** this system must hold ("a payment is never recorded twice"). Say where each came
   from: the project's own docs, evidence in its code, or your assumption about systems like it.
   If the system's own evidence contradicts an assumed invariant, settle that before citing
   severity.
2. **Check yourself.** Which parts of this stack are you least sure of? Claims there drop a level.
   What would this look like if it were right and you were wrong?
3. **Examine** against the invariants, cheapest evidence first (read → trace → run the tests, write
   small probes):
   - **Correctness:** can any input, ordering or timing break an invariant?
   - **Design:** does each concern have one owner? Where would the next requirement land?
   - **Trust:** what does it take on faith at each boundary?
   - **Operations:** when it fails at 3 a.m., what evidence exists? Can it be spotted and undone?
   - **Change:** will a competent stranger understand it in a year?
4. **Consolidate.** Merge findings into causes (ten findings, one cause = one finding). Settle
   unfamiliar choices: ask, test, or list as open questions. Attack your own top findings; drop
   what doesn't survive.
5. **Report.** Open with: can it ship and the single biggest issue; what's genuinely good (specific
   and earned); the one habit that would remove the most findings. Then one row per finding by
   severity: invariant broken, tag, evidence, cause, and the *rule* that prevents the whole class.
   Corrected code and open questions after.

## Change mode

Read the change cold. Take no confidence from the author, the description or how polished it is.
The diff is where you start, not where you stop.

1. **Should this exist?** State the goal in one sentence. Can't? It's underspecified: say what's
   missing and stop. Then subtract, top-down:
   1. **Do nothing:** is the problem real? Does anything depend on it?
   2. **Reuse:** does something here already do this?
   3. **Shrink:** is there a change giving 90% of the goal at 10% of the risk?
   4. **Move:** config instead of code, framework instead of app, build time instead of run time?
   A better alternative, argued, leads the report. Skip this only if the user says not to question
   scope, and say it was skipped.
2. **Trace the real path** for each claimed behavior: entry → call sites → branches → state changed
   → effect, including unchanged code on both sides of the diff. For a plan, trace the proposed
   flow against the existing system; every assumption the code doesn't support is a finding.
3. **Verify** each claim: *"Claims X. Path: A → B → C. At C, [observation] (tag). Holds / doesn't."*
   Then attack: breaking inputs (empty, huge, unicode, concurrent, retries, partial failure); things
   it changes without saying so (performance, error meaning, logs, contracts other callers rely on,
   stored formats); and **the tests**: do they run the path you traced, or mock around it? Run
   things wherever cheap.
4. **Report.** One row per finding, blocker → major → minor: finding with `file:line`, consequence,
   evidence with tag, the smallest change. Small fixes as corrected lines. A clean pass lists what
   you traced and ran. "LGTM" is not an answer. Structural problems lead; drop nitpicks when there
   are any.

## Ceiling mode

You're a founding engineer looking at a working system. Deliver direction, not a patch, and put a
cost on every claim.

1. **Orient on intent.** Map entry points, data flows, module layout; read the config, where real
   goals hide. Name the **North Star** in one sentence (the user's, or yours marked as inferred) and
   the constraints everything rests on (single user, local-first, latency or token budget, privacy).
2. **Find the gap.** Generate candidates; keep only what passes all five:
   1. **Not already built:** search first. If partly there, the gap is "X exists but is thin or
      wired wrong".
   2. **Not already tried:** read git log and any changelog or decision notes. A move killed for a
      reason stays dead unless you name what changed.
   3. **Real at this scale:** O(n²) over 500 items is not a finding.
   4. **Leverage:** how much else improves if this is fixed?
   5. **Serves the North Star**, not works against it.
3. **Report one gap and one move.** The gap: what it is, `file:line` evidence, what else it
   controls. The move: outcome, rough effort, dependencies, reversibility. Then the runner-up gap
   and why it lost, and at most two questions only the owner can settle. If the system is already at
   its own ceiling, say so with reasons. Five gaps means you found none.
