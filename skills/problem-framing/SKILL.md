---
name: problem-framing
description: Turn a vague idea into a buildable, testable problem brief before any architecture or code exists. Use when a new project's goal is still vague, requirements feel fuzzy or contradictory, or a build drifted and nobody can say what "done" means.
---

# Problem Framing

You refuse to build the wrong thing efficiently. The output is not code or architecture. It is a
**problem brief** precise enough that someone who never saw this conversation could build from it.

## Phases

### 1. Extract
From the user's words and any existing code or docs:
- **The job:** what should be true afterwards, as a change in the world, not a feature. ("Sales
  staff stop re-typing orders", not "build an order form.")
- **Who touches it:** people, other systems, AI agents. Machine users need parseable errors and
  stable formats.
- **What already exists:** read it before asking. A question the files answer is wasted.

### 2. Settle unknowns (ask at most one question)
Rank each unknown by how much its answer changes the build:
1. Changes direction ("one user, or many organizations?")
2. Removes the biggest unknown nobody can settle by reading
3. Sets the edges (what's out of scope)
4. Preference (names, colours)

Rank 4: pick a default, mark it *assumed*, move on. Ranks 2–3: state the reading you took and the
one you didn't, and continue. Only rank 1 becomes a question, and only when guessing wrong costs more
than asking. **One question, not five**, and frame everything it doesn't block in the same response.
No one to ask (an unattended run): take the likeliest reading, mark it *assumed* and put it first in
the brief.
A list of questions with nothing framed is this skill failing.

*Test:* the response contains at most one question, and the framing for everything that question doesn't block.

### 3. Constrain
- **Invariants:** if broken, the project failed. Each must be testable. Changing one needs the
  owner's explicit agreement.
- **Preferences:** everything else; tradeable during the build.
- **Not building:** a short list of plausible things deliberately left out. It stops scope creep
  later.

### 4. Specify
Turn every invariant into an acceptance criterion a machine could check. Banned words: *fast, clean,
intuitive, robust, scalable, user-friendly*. Name a measurement and threshold, or an observable
behavior:

*Test:* none of the banned words survives in a criterion, and each one could be checked by someone who never read the code.

> ❌ "Search should be fast."
> ✅ "Search over 10k records returns first results in under 300 ms on target hardware. (assumed: 10k is the realistic ceiling)"

Include what happens on bad input, partial failure, and empty states. A spec that only describes
success is half a spec.

### 5. Deliver the brief
Inline in the response, unless the user wants a file or another skill or an unattended run will
build from it: then write it to `BRIEF.md` at the repo root, so it survives the context.

1. The job, one plain paragraph
2. Who touches it
3. Invariants, numbered, each with its acceptance criterion
4. Preferences, numbered, marked tradeable
5. Not building
6. Open questions the owner must eventually answer
7. Assumptions: `assumption | default chosen | cost if wrong`
8. `## Decisions`: one line each, `- YYYY-MM-DD · decision: reason`, for every choice the owner made
   that the code alone would not tell a stranger (a format, a vendor, a scope cut)

Open with the job and the assumption that costs most if wrong. The acceptance criteria are what
`verify-loop` turns into the exit check; name that as the next step.

## Keeping the brief current

A brief written once and never touched is how a project forgets what its owner wants. Whenever the
owner states or changes a decision, even in passing ("FYI, they take JSON now"), write it into
`BRIEF.md` in the same sitting, before the work that acts on it. Whoever is working does this, not
only this skill.

- **Replace, don't pile up.** A decision that overrides an older one replaces its line and names what
  it replaced: `- 2026-10-09 · Export is JSON only: new bookkeeping tool. Replaces CSV (2026-09-02).`
  Move the old line, dated and with why it was retired, to `BRIEF.archive.md`. The same goes for an
  invariant or preference the decision overturns. `BRIEF.md` lists only what is true now.
- **Stay readable.** About 120 lines and 25 decisions at most. Past that, retire what no longer
  constrains the work to the archive. `context_budget.py` (in `recall`'s scripts) measures it.
- **Make it found.** The project's agent instruction file (`CLAUDE.md`, `AGENTS.md`) needs a
  start-here block that sends a fresh session to `BRIEF.md` first; `project-setup` owns its shape.

*Test:* every decision the owner stated this session is a line in `BRIEF.md`, and no line there
contradicts it.

## Rules

- A requirement said twice in different words is one requirement.
- If a new request contradicts an existing invariant, say so; don't silently take the latest one.
- Stop when there's enough to start designing. Framing that starts designing has gone too far.

## Common mistakes

Feature lists posing as requirements; twenty questions when three would change the build; specs
silent on failure; assumptions and decisions that live only in the chat.
