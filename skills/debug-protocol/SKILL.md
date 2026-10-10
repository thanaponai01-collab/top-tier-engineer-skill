---
name: debug-protocol
description: >-
  Find the proven root cause before fixing. Use when something is broken and the cause is unknown: wrong output, crash, hang, flaky, "it worked yesterday".
metadata:
  stage: fix
  card: "broken and the cause is unknown"
---

# Debug Protocol

Diagnosis ends when the cause is **named and proven**. For a diagnosis-only request, restore probe
edits and report the cause. When the user also requests a fix, continue with the regression handoff
below after proving the cause. Mixing diagnosis and fixing hides whether the cause survives.

## Rules

1. **No fixing while diagnosing.** Until the cause is proven, every code change exists only to learn
   something and is reverted after the measurement. "I changed something and it went away" means
   the symptom moved.
2. **A cause must pass in both directions.** With the cause present, the failure happens on demand.
   With only the cause removed, the same trigger no longer fails. One direction only is a
   coincidence.
3. **One change per experiment.** Write down every experiment, including dead ends, so nobody walks
   into them again. Probe edits go on a clean tree or a scratch branch, so an interrupted run leaves
   nothing behind.
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

Budget: about five experiments. When a second experiment refutes the same idea, your model of the
system is wrong; go back to Localize and re-observe rather than try a third variation. At the
budget, stop and report what is ruled out, what is still open and the next experiment you would run.

### 5. Prove
Run the two-direction test from Rule 2 and paste both results. If the environment can't run the
decisive experiment, say so plainly and give the one command that would settle it.

*Test:* both directions were run and both outputs are in the report.

### 6. Report
- The failure signature, the proven cause in one sentence, and why it wasn't caught earlier (no
  test, a guard never connected, a false assumption, missing logging).
- A table of hypotheses including dead ends: hypothesis, experiment, result, verdict.
- The minimal reproduction, written as the future regression test.

### Regression handoff when a fix is requested

Turn the minimal reproduction into a check against the requirement and actual entry point. Run it
on the original bug and retain the specific expected-versus-actual rejection before fixing code.
Include adjacent behavior that must remain working. Probe output alone is not a regression check.

Reusable proof: for requested reusable regression evidence, hand the regression to `verify-loop`:
load that skill, follow its references/handoff.md and record the rejection and strict green through
its bundled `verify.py`. Direct output files are the fallback only when verify-loop is not
installed. The wrong state is the proven cause, retained as the rejection before the fix (or
reintroduced by challenge in a scratch copy). Diagnosis only leaves a runnable regression proposal
and the captured experiments; strict green is not the diagnosis completion gate. No project-setup,
commit, CI or release is required by this handoff. Report the cause, check edits, regression result
and coverage limits separately from the diagnosis experiments.

## Common mistakes

Fixing where the symptom shows up instead of where it starts; closing as "cannot reproduce";
reading the same code harder instead of running an experiment.

Project memory: retrieve missing facts with `project-context`; after authorized changes use
`project-update` for affected records. Without helpers, follow/update existing notes directly;
read-only reviews report gaps. Skip upkeep when no durable fact changed.
