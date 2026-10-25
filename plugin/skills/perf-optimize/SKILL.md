---
name: perf-optimize
description: >-
  Make a system measurably faster or cheaper by finding the real cause. Use for slow, laggy, "speed up", "reduce cost", "will this query scale?"
disable-model-invocation: true
metadata:
  stage: fix
  card: "slow, clunky or expensive"
---

# Performance & Optimization

**Goal:** say how long the work takes now, how that grows with its input, and where the time goes,
from runs, not from reading. When asked to make it faster, every kept change prints exactly what the
code printed before, beats the noise, and was aimed at something the profile showed, and a check
left in the suite fails when the gain is taken back out. A fast wrong answer is worth less than a
slow right one. How you find the cause is yours: read it all if it fits, profile, count queries.
What counts as done is checked by the helper. `P` is
`python <this skill's base directory>/scripts/perf.py <repo>`.

Run `P --gate` whenever you like; it says which stage is open and what fixes it, and prints the
answer once all three hold (`PERF-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Measure** | `P --measure "<cmd>" --size <N>` timed a workload that prints its result on the code as it was, in a throwaway copy, and profiled one run (a size whose run takes over 20 s is timed once and not profiled). Two sizes are measured, so growth shows: make the bigger input in a scratch folder if there is none. A workload that prints differently between runs is refused. The tree as it was is kept in `.perf/before/` |
| **2. Change** | Diagnosis only: no product file changed. After a change, every workload prints exactly what it printed before, and its slowest run now beats the fastest run of the code as it was (runs alternated, unless the gain is three times past the recorded range). Every changed function held at least 2% of a profile, or has `- FILE::FUNC: <why the gain needs it>` in `.perf/notes.md` |
| **3. Guard** | After a change, `P --gate --guard "<test cmd>"` saw the guard pass now and fail with each changed file put back alone. A count of calls, file opens or queries holds better than a stopwatch; a time needs a big input and room to spare |

Fix only when asked. Saved numbers with nothing to run here are judged by
[benchmark validity](references/benchmark-validity.md), and the answer says nothing was run.
A query said to use an index quotes the plan line (`EXPLAIN`, or the engine's own); adding an
index to a populated table is a migration, with its way back written before it runs.
Report the drafted answer with its `[[fill: ...]]` slots filled. Keep the guard; delete `.perf/`
afterwards, or commit it with the change.
