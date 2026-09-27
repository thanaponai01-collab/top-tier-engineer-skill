---
name: agent-prove
description: Prove an AI agent meets a stated bar over repeated runs, not one, and catch regressions when it changes. Use after an agent's evals exist and the build is in place, before shipping one, when an agent is "flaky", or after any model, prompt or tool change.
---

# Agent Prove

One pass is an anecdote. An agent is proven when the same task set, run several times, clears a bar
written down before the run. Needs the task set and graders from `agent-evals`; if they do not exist,
build those first.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Steps

1. **State the bar before running.** For example "95% of tasks pass, none of the safety tasks fail,
   under N seconds and $X a task". Write it in `evals/<agent>/bar.md`, with a total spend ceiling for
   the proving. Never move the bar to fit the result.
2. **Run the whole set several times.** 5 or more runs per task for anything with variance. Record
   pass rate per task, the spread across runs, cost and latency in `evals/<agent>/runs/`. Report a
   rate, not a single pass. If the spend ceiling is reached first, stop and report the runs you have.
3. **Read the failures.** Open the transcripts of the tasks that failed most. A task that fails
   sometimes is a different problem from one that always fails: the first is missing information or
   an ambiguous instruction, the second is a wrong tool or a wrong grader.
4. **Compare to the last baseline** (the latest file in `runs/`). A change that lifts one task and drops two is a regression.
   Name what got worse. Keep a fix inside the files it named with `verify.py scope` from `verify-loop`.
5. **Run the held-out slice once, at the end,** and report it separately. If it is far below the tuned
   set, the agent learned the set, not the task.
6. **Attack it.** Run the abuse cases from `threat-model` (injected instructions in tool results,
   the worst tool call, data leaving through outputs) as tasks that must pass. A safety task that fails
   blocks the release whatever the rate is.
7. **If the bar is not met,** say what passes, what fails and what you would try, and stop. Do not
   lower the bar.

*Test:* the bar was written before the run, and the report has a rate over repeats.

## Report

Verdict first: met or not, on which set, over how many runs. Then rate and spread, safety tasks,
cost and latency, the worst failures with transcript evidence, and what was not tested.

## Common mistakes

One lucky run; averaging away a safety failure; lowering the bar after seeing the number; reading
only the score; skipping the held-out slice; re-running until it passes.

## Next

Ready to ship: `agent-release`. Wider software correctness around the agent: `correctness-gate`.
Without those loaded, do the step plainly and say the skill was missing.
