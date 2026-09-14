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

### 2. Stabilize
Shrink the reproduction: smallest input, fewest steps, least state. For intermittent failures, find
what makes them consistent (load, ordering, timing) before going further.

### 3. Localize
Halve the search space along whichever axis is cheapest:
- **Place:** which layer or function does the bad value first appear in? Check the middle of the
  data's path.
- **Time:** which change introduced it? Bisect the commits. "It worked yesterday" is a gift.
- **Input:** which part of the input sets it off? Bisect the minimal failing input.

Use the system's own logs, REPL and tests before adding logging. When still unsure, stop the
program at the suspect point and read the real state (debugger, crash dump, memory profiler) instead
of inferring it from source.

### 4. Hypothesize
One sentence that could be proven wrong: *"X fails because Y, so experiment Z will show W."* Before
blaming code that looks odd, check git history for why it was written that way.

### 5. Prove
Run the two-direction test from Rule 2 and paste both results. If the environment can't run the
decisive experiment, say so plainly and give the one command that would settle it.

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
