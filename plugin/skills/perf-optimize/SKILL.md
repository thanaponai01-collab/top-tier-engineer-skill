---
name: perf-optimize
description: >-
  Make code measurably faster or cheaper by finding where the time really goes. Use for slow, laggy, "speed up", "reduce cost", "will this scale?"
disable-model-invocation: true
metadata:
  stage: fix
  card: "slow, clunky or expensive"
---

# Performance & Optimization

Say how long the work takes now, how that grows as the input grows, and where the time goes, all
from runs, not from reading the code. When asked to make it faster, make it faster without changing
what it produces. A fast wrong answer is worth less than a slow right one. How you find the cause is
up to you.

**What done looks like**

- The work was timed on the code as it was, at two or more input sizes, so the growth is measured
  (make a bigger input in a scratch folder if there is none), and one run was profiled or its
  queries, file opens or calls counted.
- Fix only when asked. Each kept change prints exactly what the code printed before, and its gain
  is clear of the noise: runs of the old and new code alternated, slowest new run under the fastest
  old one, or a gain far past the spread.
- Each change goes at something the measurement showed. A change that touched nothing the profile
  pointed at is taken out, or the answer says why the gain needs it.
- A check stays in the test suite that fails when the gain is taken back out. A count of calls,
  file opens or queries holds better than a stopwatch; a timing needs a big input and room to spare.

**Avoid**

- Calling a change faster when the old and new runs did different work: zero useful work, errors
  dropped, wrong output, or a debug build against a release build. Those are rejected, not wins.
- Turning a gain inside the noise into a win. Say it is inconclusive and name the next experiment.
- Claiming a run that did not happen. Saved numbers with nothing to run here can be judged, and the
  answer says nothing was run.
- Saying a query uses an index without quoting the plan line (`EXPLAIN` or the engine's own).
  Adding an index to a table that already holds data is a migration: write its way back first.

**The answer**

```
- `<command>` at size <N>: before <median, spread>; after <median, spread>, output identical
  (one line per command and size; no "after" when nothing changed)
Growth: from size <A> to <B> (<x>), time grew <y>: <in step with / faster than / slower than> the input
Where the time went at size <B>: <function share% (calls)>; ...
Changed: <function>: <X cost Y because Z; now W>        (or: Diagnosis only: <cause; the fix and what it should cut>)
Guard: `<test command>` passes now and fails with the change taken back out
Not measured: <sizes, machines, cold starts or paths no run here covered>
```
