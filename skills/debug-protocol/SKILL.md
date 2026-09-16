---
name: debug-protocol
description: Find the proven root cause of an observed failure before fixing it. Use when something is broken and the cause is UNKNOWN: errors, wrong output, crashes, hangs, flaky behavior, "it worked yesterday", or a previous fix that didn't hold.
---

# Debug Protocol

Debugging is not fixing. This skill ends when the cause is **named and proven**. Mixing diagnosis
and fixing is how symptoms get patched while the cause survives.

## Rules

1. **No fixing while diagnosing.** Until the cause is proven, every code change exists only to learn
   something and is reverted after the measurement. "I changed something and it went away" means
   the symptom moved.
2. **A cause must pass in both directions.** With the cause present, the failure happens on demand.
   With only the cause removed, the same trigger no longer fails. One direction only is a
   coincidence.
3. **One change per experiment.** Write down every experiment, including dead ends, so nobody walks
   into them again.
4. **Reproduce before you theorize.** A failure you can't reproduce is still real: don't close it
   and don't guess a fix. Add the log, metric or probe that captures it next time, and treat that
   capture as the reproduction.

## Phases

### 1. Reproduce
Make the failure happen on demand under recorded conditions (input, environment, state, timing).
Capture the exact signature: message, wrong value, stack. If you can't reproduce it, stop and say
what log, metric or probe would make it reproducible.

*Test:* someone else could make it fail from your written conditions alone.

### 2. Stabilize
Shrink the reproduction: smallest input, fewest steps, least state. For intermittent failures, find
what makes them consistent (load, ordering, timing) before going further.

### 3. Localize
Halve the search space along whichever axis is cheapest:
- **Place:** which layer or function does the bad value first appear in? Check the middle of the
  data's path.
- **Time:** which change introduced it? Bisect the commits. "It worked yesterday" is a gift.
- **Input:** which part of the input sets it off? Bisect the minimal failing input.

*Test:* you can name where the bad value is first wrong, which is rarely where it was noticed.

Use the system's own logs, REPL and tests before adding logging. When still unsure, stop the
program at the suspect point and read the real state (debugger, crash dump, memory profiler) instead
of inferring it from source.

### 4. Hypothesize
One sentence that could be proven wrong: *"X fails because Y, so experiment Z will show W."* Before
blaming code that looks odd, check git history for why it was written that way.

### 5. Prove
Run the two-direction test from Rule 2 and paste both results. If the environment can't run the
decisive experiment, say so plainly and give the one command that would settle it.

*Test:* both directions were run and both outputs are in the report.

### 6. Report
- The failure signature, the proven cause in one sentence, and why it wasn't caught earlier (no
  test, a guard never connected, a false assumption, missing logging).
- A table of hypotheses including dead ends: hypothesis, experiment, result, verdict.
- The minimal reproduction, written as the future regression test.

When the fix is small and obvious, deliver it in the same response, clearly separated from the
diagnosis, with the regression test.

## Common mistakes

Fixing where the symptom shows up instead of where it starts; closing as "cannot reproduce";
reading the same code harder instead of running an experiment.
