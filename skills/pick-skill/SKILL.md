---
name: pick-skill
description: Choose which engineering skill the work in front of you needs, and say what each one will and will not do. Use when more than one could apply, when the ask is broad ("look at my codebase", "make this better", "is this good?", "what should I do next?"), when you don't know where to start, or when someone asks which skill to run.
---

# Pick a Skill

Sixteen skills answer sixteen different questions, and five of them answer questions that sound
identical from outside. This is the map. It is one decision, then you leave.

**Route on the question, not the words.** "Review my code" is five different jobs depending on what
the asker wants to know. Ask yourself what answer would end the conversation, and route to that.

**Routing is not the work.** Name the skill, say in one line why that one, and start it. Never
present the menu and stop — a routing answer with no work started is this skill failing.
*Test:* the response that names a skill also begins it.

**No skill fitting is an answer.** A typo, a rename, a config value, a question about what the code
does — do it directly and say so. Sixteen skills are for work that is worth the ritual.
*Test:* you can say what this skill would add that doing the work plainly would not.

## "Look at my code and tell me what's wrong"

Five skills land here. They differ by the question underneath, and picking the wrong one gives a
real answer to a question nobody asked.

| What the asker wants to know | Skill | What comes back |
|---|---|---|
| What should I fix first? | `senior-review` | everything that matters, ranked by consequence, and the skill to run on the biggest gap |
| Should this change land? | `scrutinize` | one diff, PR or plan read cold: ship / fix-then-ship / rework / reject |
| Is the structure itself wrong? | `arch-design` (audit mode) | duplicated systems, layers built for a future that never came, the moves that fix the most |
| Is it tangled — with numbers? | `structure-gate` | measured complexity, nesting, length, cycles, duplication, and how much was too opaque to measure |
| What can I safely delete? | `latent-audit` | dead code proven dead before anything is deleted, plus layer breaches |

Still ambiguous after that? `senior-review` — it is the one that ends by naming the next skill.

## Everything else

| The situation | Skill |
|---|---|
| A vague idea, or nobody can say what "done" means | `problem-framing` |
| Choosing a stack, a boundary, a pattern | `arch-design` (design mode) |
| "Show me the architecture" / before → after / where the problems sit | `arch-map` |
| Planned work needs to reach another machine or another person | `issue-handoff` |
| Writing the code | `build-discipline` |
| Built, but nothing happens when you run it | `wire-check` |
| Broken, cause **unknown** | `debug-protocol` |
| Broken, cause **known** — or upgrade, refactor, deprecate | `evolve-maintain` |
| Slow, clunky, expensive, "will this query scale?" | `perf-optimize` |
| Auth, secrets, untrusted input, "can this be abused?" | `threat-model` |
| "Does it actually work?" before a merge or release | `correctness-gate` |
| Deploying, or changing the shape of stored data | `safe-release` |

## The four flows

Every flow has the same shape: **find → change → prove → ship**.

| Goal | Find | Change | Prove | Ship |
|---|---|---|---|---|
| Build something new | `problem-framing` → `arch-design` | `build-discipline` | `correctness-gate` | `safe-release` |
| Clean up a messy codebase | `arch-design` (audit) → `arch-map` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Fix a bug | `debug-protocol` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Make it faster or safer | `perf-optimize` / `threat-model` | same skill | `correctness-gate` | `safe-release` |

A flow is a route, not a queue. Run the next skill when the work reaches it, not because the table
says so — and never re-run a step whose job the last skill already did.

## Three traps

**Broad ask, whole-repo sweep.** "Have a look at my codebase" is not permission to read all of it.
Name the area and the question in one line, route on that, and say what you scoped out.
*Test:* you can name what you deliberately did not read.

**Routing to the ritual instead of the work.** `build-discipline` already wires and proves each
slice; following it with `wire-check` and `correctness-gate` on the same slice is the same check
paid for three times. Those two are for code that arrived without them.
*Test:* the skill you are about to run would find something the last one could not have.

**Symptom words pointing at the wrong skill.** "It's slow" with an unknown cause is
`debug-protocol`, not `perf-optimize`. "It's insecure" with a reported breach is `debug-protocol`
first. Route on what is known, not on the adjective.
*Test:* you can say whether the cause is known, and your route follows that answer.

## Report

One line: the skill, and the question it is going to answer. Then run it. If two skills genuinely
both apply, say which one runs first and why the other waits — never run both at once.
