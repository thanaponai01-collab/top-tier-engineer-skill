---
name: agent-evals
description: >-
  Build the check for an AI agent or model-driven feature before the agent exists: a task set, a grader the agent cannot touch, and proof the grader can fail. Use at the start of any agent or LLM feature, when "it worked when I tried it" is the only evidence, or when an agent's failures are hard to pin down.
metadata:
  stage: build
  card: "evals and a grader before building an agent"
---

# Agent Evals

A model-driven system changes from run to run, so one green run proves nothing. The check that
does hold is a fixed set of tasks and a grader that did not come from the agent. Build both before
the agent, and keep them out of its reach. This is `verify-loop`'s "build the check first" applied
to something non-deterministic; read that skill for the VERIFY.md format and the baseline.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Steps

1. **Name the claim.** What a finished task looks like, observable from outside, and what the agent
   must refuse. Read the refusal list straight from `agent-design`'s tool contract
   (`docs/agent-design.md`) if one exists — it names the one-way tools and the untrusted-content tools
   the refusal and injection tasks below come from. If neither the claim nor a tool contract can be
   said, run `problem-framing` then `agent-design` first.
2. **Write the task set** in `evals/<agent>/tasks.*`. Aim for 20 inputs, never fewer than 12: real
   ones where you have them, otherwise realistic. Include the ambiguous, the hostile and the ones
   that should be refused. Set aside a held-out slice (a quarter of them) that nobody tunes against.
3. **Write a grader per task.** Prefer, in order: a state check on the real system after the run (the
   row exists, the file changed, the refund was not issued); a schema or exact check on the output; a
   rubric graded by a fresh context that sees the task, the output and the rubric, never the agent's
   reasoning. Grade the outcome, and separately the path (tools called, steps, cost) where the path
   matters.
4. **Prove the grader can fail.** Run it against an empty agent and a deliberately wrong one. Both
   must score low, and for each you can name the task that failed and why. A grader that passes a
   wrong agent is the bug. Give it three attempts to fix; then stop and report which tasks the wrong
   agent still passes, instead of grinding on.
5. **Freeze it.** `verify.py baseline` from `verify-loop`, so the grader and task set are never edited
   to make a run pass. A grader believed wrong is a finding for a person, not an edit.

*Test:* the agent's author did not write the graders, and you can name a run that scored 0.

## Common mistakes

Writing the grader from what the agent happened to output; only happy-path tasks; grading text when
the state could be checked; a rubric grader that sees the agent's reasoning; tuning against the
held-out slice; fewer than 12 tasks, where one flake moves the score by several points.

## Next

The tools and prompt are built against this set with `build-discipline`. Proof over repeated runs is
`agent-prove`. Without `verify-loop` loaded, keep the task set and graders in one file the agent
cannot edit, and say so in the report.
