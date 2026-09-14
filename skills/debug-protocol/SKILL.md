---
name: debug-protocol
description: >
  Localize an observed failure to its proven root cause before any fix. Use when something is broken and the cause is UNKNOWN — errors, wrong output, crashes, hangs, flaky behavior, "it worked yesterday" — or when a previous fix didn't hold.
---

# Debug Protocol

> **The question:** Why is it wrong?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

known-cause fixes → `evolve-maintain`; "is it even connected?" questions → `wire-check`; working-but-slow → `symptom-audit` or `perf-optimize`. Where the environment also carries a skill specialised in *constructing* a fast, deterministic pass/fail repro loop, Phase 1 may delegate to it and return here — the loop is a tactic, and this skill still owns the two-way proof that names the cause.

Debugging is not fixing. This skill ends when the cause of the failure is **named and proven** —
the fix is a separate job with its own rules. Mixing the two is how symptoms get patched while the
cause survives.

Where it sits among the others: `wire-check` asks *"is it connected?"*, `correctness-gate` asks
*"is it right?"*, `senior-review` asks *"is it a good design?"*, `symptom-audit` asks *"where does
the slowness the user feels actually come from?"* — this skill asks *"why is it wrong?"*. Working
but slow is not wrong.
Shared vocabulary and laws: `PROTOCOL.md` at the suite root.

## The job

1. **No fixing while diagnosing.** Until the cause is proven, every code change exists only to
   learn something, and is reverted after you take the measurement. "I changed something and it
   went away" means the symptom moved, not that you found the cause.
2. **A cause has to pass the test in both directions.** With the cause present, the failure
   happens on demand **(proven)**; with only the cause removed, the same trigger no longer fails
   **(proven)**. Something that passes in one direction only is a coincidence, not a cause.
3. **Change one thing per experiment.** Each test changes exactly one thing; change two and you
   cannot tell which one mattered. Write down every experiment, including the ones that led
   nowhere — a dead end you recorded is one nobody walks into again.
4. **No bug is real until you can reproduce it.** A report you cannot reproduce is a finding about
   missing logging or metrics, not something to debug (see Phase 1).

## Steps: Reproduce → Stabilize → Localize → Hypothesize → Prove → Hand off

### Phase 1 — Reproduce

Make the failure happen on demand, under recorded conditions (input, environment, state, timing).
Capture the exact failure signature — message, wrong value, stack, observable difference from
expected. If you genuinely cannot reproduce it: stop, report **`CAUSE: blocked(unreproduced)`**, and hand it
to `evolve-maintain` to add the log, metric, or probe that would make it reproducible. Debugging a
complaint you cannot reproduce is guessing with a debugger open.

### Phase 2 — Stabilize

Shrink the reproduction to its minimum: smallest input, fewest steps, shortest time, least state.
For failures that come and go, find what makes them consistent first — the load, the ordering, or
the timing that takes it from 1-in-50 to every time. An intermittent reproduction makes Phase 5's
two-direction test a statistics problem; a consistent one makes it a single command.

### Phase 3 — Localize (bisection over three axes)

Cut the search space in half repeatedly along whichever axis is cheapest to cut:

- **Place** — which layer, module, or function does the bad value first appear in? Check the middle
  of the data's path: good going in and bad coming out halves the suspects.
- **Time** — which change introduced it? If there is version history, bisect the commits. "It
  worked yesterday" is a gift — take it literally.
- **Input** — which part of the input sets it off? Bisect the smallest failing input from Phase 2.

Use what the system already gives you — its logs, its REPL, its tests — before adding logging of
your own; logging you added that turned out to help is kept, and named in Phase 6 as an
improvement. When logs and static checks still leave you unsure where the value goes bad, stop the
program and look: pause at the suspect point and read the real state there — variable values, the
call stack that reached it, memory or allocation state for a leak — instead of working it out from
the source. Find whatever this runtime offers for that (its debugger, its crash-dump reader, its
memory profiler) the same way wire-check works out how a framework wires things; naming one
specific tool here would date this file (Discipline 6). State you watched at runtime is
**(proven)** for what it showed; state you worked out by reading code is **(trace-only)**.

### Phase 4 — Hypothesize

State the suspected cause in one sentence that could be proven wrong: *"X fails because Y, so
experiment Z will show W."* A guess that doesn't predict something you can observe is a hunch, not
a hypothesis. Apply Law 3 before blaming code you don't recognise: odd-looking is not guilty —
check `DECISION_LEDGER.md` for why it was written that way.

### Phase 5 — Prove

Run the two-direction test from Rule 2 above. Run both directions; paste both results.
Only then is the cause **(proven)**. If the environment cannot execute the decisive experiment,
the verdict caps at **(trace-only)** with that limitation stated in bold and the single command
that would promote it.

### Phase 6 — Hand off

Produce the **Cause Verdict** (in the report, and as the root-cause input to `evolve-maintain`):

1. Failure signature and minimal reproduction (the future regression test, pre-written).
2. Proven cause — the two-way test results, verbatim excerpts.
3. Why it wasn't caught earlier — no oracle, a guard that was never connected, an assumption that
   turned out false, missing logging. This line decides which skill gets the prevention work.
4. Experiment log — every hypothesis tried, including the ones that led nowhere.
5. Verdict line: a `CAUSE` line per PROTOCOL §5 — `findings(<cause>, <tag>)`, or `blocked` when unreproduced.

**Verdict noun:** `CAUSE`

The fix routes to `evolve-maintain` (which classifies it and executes via `build-discipline` +
`correctness-gate`). This skill never ships the fix on its own — but per Law 5 (the diagnosis ships with the fix), when
the fix is small and obvious, hand off and fix in the same response, keeping the two clearly
separate.

## Common mistakes

Fixing the symptom where it *shows up* instead of where it *starts*; closing a bug as "cannot
reproduce"; reading the same code harder instead of running an experiment.
