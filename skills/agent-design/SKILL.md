---
name: agent-design
description: Design an AI agent's tool surface, reversibility per tool, and context/memory strategy before any agent code or eval exists. Use when nobody has written down what tools the agent gets, what untrusted content flows into its context, or what it must never be allowed to do without a human confirm.
---

# Agent Design

`agent-evals` needs a claim to test and `threat-model` needs abuse cases to write — both stall without
something to read from. That something is the tool contract this skill produces: every tool the agent
can call, what each one can do to the world, and what content flows back into the agent's context from
each. Skip this and the tool surface gets designed by accident, one `if` statement at a time, as the
agent is built.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain · **suspected** = neither.*

## Steps

1. **Name the loop shape.** One agent, or an orchestrator handing off to subagents? For each: who owns
   the final output, and who owns the human confirm on a one-way action — one owner per irreversible
   action, never "whichever agent gets there first."

2. **List every tool, before any is built.** For each tool, in one row: what it does, its reversibility
   tier from `PHILOSOPHY.md` habit 5 (reversible: act; one-way: needs a human confirm, and a yes for one
   call never covers the next), and what it hands back into the agent's context. That last column is the
   one people skip: a tool that returns a fetched page, a file, another user's message, or any text you
   did not write yourself is handing the agent content an attacker could have shaped. Mark those rows —
   `threat-model` and `agent-prove`'s abuse cases start from exactly this list.

3. **Decide the context and memory strategy.** What persists across turns, what gets summarized or
   dropped, and — the question most designs skip — what must never cross a boundary: between users,
   tenants, or sessions. Name the boundary as a sentence a test can check ("session B's tool results
   never appear in session A's context"), not as an assumption about the framework.

4. **Write the tool contract to one file**, `docs/agent-design.md`: the loop shape, the tool table from
   step 2, and the context boundary from step 3. This is the file `agent-evals` step 1 and
   `threat-model`'s tool-surface pass both read instead of re-deriving the tool list from the code.

5. **Draw the must-refuse list from the contract, not from imagination.** Every one-way tool earns at
   least one refusal case (the agent declines, or stops for confirm, when the task tries to use it
   without grounds); every marked row earns an injection case (hostile content inside that tool's result
   tries to redirect the agent). A refusal case naming a tool that is not in the table is a guess, not a
   spec — add the tool to the table first.

*Test:* every tool the agent can call appears in the table with a reversibility tier and a context
column, and every one-way tool has at least one refusal case named against it.

## Common mistakes

Writing the tool list from the code after the agent is half-built, so the design ratifies whatever
shipped rather than deciding it; a tool's context column left blank because "it's just an API call" —
the question is what the API call returns, not who calls it; one "human confirm" step that covers every
one-way tool instead of one per action; skipping straight to `agent-evals` with no tool contract, so its
must-refuse tasks are invented rather than derived.

## Next

The task set and grader built against this contract: `agent-evals`. The tool-surface abuse cases this
contract makes concrete: `threat-model`. Building the tools and the loop: `build-discipline`. Without
`agent-evals` or `threat-model` loaded, keep the tool contract in `docs/agent-design.md` anyway and say
in the report which of the two steps above was done from it by hand instead.
