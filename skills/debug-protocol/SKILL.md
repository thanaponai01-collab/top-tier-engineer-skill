---
name: debug-protocol
description: >
  Localize an observed failure to its proven root cause before any fix is attempted. Use whenever
  something is broken and the cause is UNKNOWN — error messages, wrong output, crashes, hangs,
  flaky or intermittent behavior, "it worked yesterday", "it works on my machine", or any bug
  report where the first question is "why?". Also trigger when a previous fix didn't hold, which
  means the original cause was never actually found. Do not use for known-cause fixes (route to
  evolve-maintain) or for "is it even connected?" questions (route to wire-check).
---

# Debug Protocol

Debugging is not fixing. This skill ends when the cause of an observed failure is **named and
proven** — the fix itself is a separate act with its own discipline. Mixing the two is how
symptoms get patched while causes survive.

Distinct mandate within the suite: `wire-check` asks *"is it connected?"*, `correctness-gate` asks
*"is it right?"*, `senior-review` asks *"is it wise?"* — `symptom-audit` asks *"where does the felt slow/clunky live?"* — this skill asks *"why is it wrong?"*; working-but-slow is not wrong
Shared vocabulary and laws: `PROTOCOL.md` at the suite root. (Gloss: **(proven)** executed · **(trace-only)** read, chain complete ·
**(suspected)** chain incomplete, flag only · **(assumed)** unverified premise — log it.)

## Operating contract

1. **No fix during diagnosis.** Until the cause is proven, every code change exists only to gain
   information and is reverted after the measurement. "I changed something and it went away" is a
   vanished symptom, not a found cause — the bug has merely moved house.
2. **A cause must pass the two-way test.** The proven cause must (a) *predict* the failure — with
   the cause present, the failure reproduces on demand **(proven)** — and (b) *predict its
   absence* — with only the cause removed, the same trigger no longer fails **(proven)**. A cause
   that passes only one direction is a correlation wearing a cause's badge.
3. **One variable per experiment.** Each probe changes exactly one thing; stacked changes produce
   unattributable evidence. Record every experiment, including the failures — a dead hypothesis
   recorded is a dead end no future model re-enters.
4. **The bug is innocent until reproduced.** An unreproducible report is an observability finding,
   not a debugging target (contract rule below).

## Pipeline: Reproduce → Stabilize → Localize → Hypothesize → Prove → Hand off

### Phase 1 — Reproduce

Make the failure happen on demand, under recorded conditions (input, environment, state, timing).
Capture the exact failure signature — message, wrong value, stack, observable difference from
expected. If reproduction fails after honest effort: stop, report **`CAUSE: unreproduced`**, and
hand to `evolve-maintain` to add the log/metric/probe that would make it reproducible. Debugging
an unreproduced complaint is guessing with a debugger attached.

### Phase 2 — Stabilize

Shrink the reproduction to its minimum: smallest input, fewest steps, shortest time, least state.
For intermittent failures, find the stabilizer first (the load, ordering, or timing condition that
takes it from 1-in-50 to every time) — an intermittent reproduction makes Phase 5's two-way test
statistically expensive; a stabilized one makes it one command.

### Phase 3 — Localize (bisection over three axes)

Cut the search space in half repeatedly along whichever axis is cheapest to cut:

- **Space** — which layer/module/function does the corruption first appear in? Probe the midpoint
  of the data's path; healthy upstream + sick downstream halves the suspects.
- **Time** — which change introduced it? If version history exists, bisect commits; "worked
  yesterday" is a gift — take it literally.
- **Input** — which property of the input triggers it? Bisect the minimal input from Phase 2.

Derive probes from *this* system's own observability (its logs, its REPL, its tests) before adding
instrumentation; added instrumentation that proves useful is kept and flagged as an observability
gain for Phase 6. When static probes and log-reads leave the corruption point ambiguous, escalate
to **runtime inspection**: pause execution at the suspect frame and read the actual program state
there — live variable values, the call stack that reached this point, heap or allocation state for
leaks — rather than inferring that state from source. Derive *this* runtime's inspection facility
(its interactive debugger, its core-dump reader, its memory profiler) the same way wire-check
derives a framework's wiring; naming a specific tool here would be a ceiling (Discipline 6). Observed
runtime state is **(proven)** for what it shows; inferred state from reading code is **(trace-only)**.

### Phase 4 — Hypothesize

State the suspected cause in one falsifiable sentence: *"X fails because Y, therefore Z experiment
will show W."* A hypothesis that doesn't predict a specific observable is intuition, not a
hypothesis. Apply Law 3 (violation ≠ deviation) before blaming unfamiliar code: strange-looking is not guilty-looking —
check `DECISION_LEDGER.md` archaeology for the fence's reason.

### Phase 5 — Prove

Run the two-way test from contract Rule 2. Both directions execute; both results are pasted.
Only then is the cause **(proven)**. If the environment cannot execute the decisive experiment,
the verdict caps at **(trace-only)** with that limitation stated in bold and the single command
that would promote it.

### Phase 6 — Hand off

Produce the **Cause Verdict** (in the report, and as the root-cause input to `evolve-maintain`):

1. Failure signature and minimal reproduction (the future regression test, pre-written).
2. Proven cause — the two-way test results, verbatim excerpts.
3. Why it wasn't caught earlier — missing oracle, unwired guard, false assumption, observability
   gap. This line decides which lifecycle skill receives the prevention work.
4. Experiment log — every hypothesis tried, including the dead ones.
5. Verdict line: `CAUSE: proven(<one-line cause>) | trace-only(<reason>) | unreproduced`.

The fix routes to `evolve-maintain` (which classifies it and executes via `build-discipline` +
`correctness-gate`). This skill never ships the fix alone — but per Law 5 (diagnosis ships with the artifact), when the fix is obvious
and small, hand off and fix in the same response, with the two acts clearly separated.

## Anti-patterns this skill exists to kill

Shotgun debugging (change things until the symptom hides); fixing the symptom at the layer where it
*appears* instead of where it *originates*; "cannot reproduce, closed"; debugging by re-reading the
same code harder instead of running an experiment; stacked changes; causes asserted from one-way
evidence; diagnosis that evaporates instead of becoming a regression test.

## Why this skill improves as models improve

Bisection, falsifiable hypotheses, and the two-way test are method, not knowledge. A stronger model
forms sharper hypotheses, designs cheaper decisive experiments, and localizes in fewer cuts —
through this same file, unchanged.
