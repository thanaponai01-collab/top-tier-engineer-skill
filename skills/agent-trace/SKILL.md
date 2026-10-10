---
name: agent-trace
description: >-
  Walk one AI agent run step by step to the exact step it went wrong. Use for "why did the agent do that?" or a transcript that looks wrong.
metadata:
  stage: fix
  card: "why did the agent do that?"
---

# Agent Trace

This skill only traces. It does not fix the agent (`debug-protocol`, `build-discipline`), does not
grade or rate it over many runs (`agent-prove`), and does not judge whether the task/grader was fair
(`agent-evals`). It ends when the divergence step is named and evidenced — nothing after that.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Steps

### 1. Get the whole trace
Every tool call with its arguments, every tool result, every reasoning/assistant turn, in order —
not a summary someone wrote after the fact. If any step is missing (a tool call logged without its
result, a truncated transcript), say exactly which step is missing and stop there rather than fill
the gap with a guess.

*Test:* you can point to the raw line/turn for every step you use below, not a paraphrase.

### 2. Walk it forward, one step at a time
For each step: state before → action taken (tool + arguments) → result received → state after. Do
this in order, without skipping to the end result first — the divergence is almost never on the
last step.

*Test:* you have a numbered list of steps, and step *N*'s "state before" matches step *N-1*'s
"state after."

### 3. Find the first step that diverges
Compare each step's action against what the task or instruction actually asked for at that point.
The divergence step is the *first* one where the agent's action or read of the world stops matching
intent — not the step where the wrong output finally showed up.

*Test:* you can name the step number and show the intended action next to the actual one.

### 4. Name the cause at that step
Pick one: wrong or missing context in the input at that point, the agent misread an instruction, the
agent trusted a bad tool result as fact, the agent picked the wrong tool, a reasoning error with no
bad input to blame, or the step is fine and only compounds a wrong earlier step (loop back to step 3
if so).

*Test:* the cause is a single sentence tied to that one step, not a general theory about the agent.

## Report

Verdict first: the divergence step (number + what it did), the cause category, one sentence why.
Then the step-by-step chain up to and including that step, quoted from the transcript, as evidence —
label each fact *proven* (read directly), *traced* (followed through the whole chain) or *suspected*
(neither). Close with what's unproven.

## Common mistakes

Summarizing the run instead of walking every step; blaming the step where the bad output *appeared*
instead of where it first went wrong; fixing or rewriting the prompt while tracing; guessing at a
missing tool result instead of naming it missing; reading only the final assistant message.

## Next

A fix for the named cause: `debug-protocol` (code) or `build-discipline` (agent build). Whether this
is a one-off or a pattern across runs: `agent-prove`. If the task or grader itself looks wrong, not
the agent: `agent-evals`.
