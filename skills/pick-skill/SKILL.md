---
name: pick-skill
description: >-
  Choose which engineering skill fits the work and say what each one will and will not do. Manual: run /pick-skill when you don't know which skill to use.
disable-model-invocation: true
metadata:
  stage: run
  card: "unsure which skill fits"
---

# Pick a Skill

Each skill answers a different question, and five of them answer questions that sound
identical from outside. This is the map. It is one decision, then you leave.

**Route on the question, not the words.** "Review my code" is five different jobs depending on what
the asker wants to know. Ask yourself what answer would end the conversation, and route to that.

**Routing is not the work.** Name the skill, say in one line why that one, and start it. Never
present the menu and stop — a routing answer with no work started is this skill failing.
*Test:* the response that names a skill also begins it.

**No skill fitting is an answer.** A typo, a rename, a config value, a question about what the code
does — do it directly and say so. The skills are for work that is worth the ritual.
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
| More than one piece to build, or work about to go to other agents: what order, and what can safely run together | `plan-work` |
| Planned work needs to reach another machine or another person | `issue-handoff` |
| Designing an AI agent before any code: tools, reversibility, what flows into its context | `agent-design` |
| Building an AI agent or model-driven feature: checks first | `agent-evals` |
| Proving an agent works over repeated runs, or after a model or prompt change | `agent-prove` |
| One agent run looks wrong and you want to know where it diverged | `agent-trace` |
| Shipping a live agent, or watching one | `agent-release` |
| A live agent has been running a while and you want to know if it drifted | `agent-drift` |
| Writing the code | `build-discipline` |
| Built, but nothing happens when you run it | `wire-check` |
| Broken, cause **unknown** | `debug-protocol` |
| Broken, cause **known** — or upgrade, refactor, deprecate | `evolve-maintain` |
| Slow, clunky, expensive, "will this query scale?" | `perf-optimize` |
| Auth, secrets, untrusted input, "can this be abused?" | `threat-model` |
| An agent needs to check its own work and loop until it passes, or you want every feature mapped to its tests | `verify-loop` |
| Learning what a system has and how to reach each feature (route, click, shortcut, command), or keeping that map current | `feature-map` |
| Why is it built this way, why was Y picked, where does this number come from, before changing code that looks wrong | `code-history` |
| Someone needs to understand a system: what it is, how it works, why (nothing gets changed) | `explain` |
| Prepare agent instructions and worker routing | `project-setup` |
| Prepare or refresh project foundation, architecture, commands and memory | `drive` |
| Understand an unfamiliar system, reuse its foundation, fill only gaps and check one prediction | `onboard-system` |
| You know the goal but not the skills, and want it carried through to done | `drive` (unattended, with a decision log: `drive-overnight`) |
| Starting or resuming work: "where were we?", what is the state and the next step | `recall` |
| "Does it actually work?" before a merge or release | `correctness-gate` |
| Deploying, or changing the shape of stored data | `safe-release` |
| Questions about saved goals, work, commands or evidence | `project-context` |
| Maintain context after work or reconcile missed updates | `project-update` |

## The Relay: nine checkpoints

Any piece of work passes the same nine checkpoints, each owned by one skill, and each leaves evidence
the next one reads. In a driven run, RUN.json is authoritative for progress and blockers; the files
below support its checks. Skip a checkpoint on purpose (a typo skips all nine),
never by accident.

| # | Checkpoint | Question | Skill | Baton |
|---|---|---|---|---|
| 1 | Orient | Where are we? What is here? | `recall` to resume, `onboard-system` on first contact | the capsule; `VERIFY.md`, `FEATURES.md`, `docs/architecture.md` |
| 2 | Frame | What does done mean? | `problem-framing`, then `verify-loop` | `BRIEF.md`; the exit check |
| 3 | Design | What shape, and what can go wrong? | `arch-design` (`agent-design` for an agent), `threat-model` | `docs/arch-design.md` |
| 4 | Plan | Which pieces, in what order, which can run together? | `plan-work` | `PLAN.md` |
| 5 | Build | Is each slice proven and wired? | `build-discipline` (`agent-evals` before any agent code) | `BUILD.md`, commits |
| 6 | Prove | Does the whole thing hold? | `correctness-gate`, `wire-check`; `agent-prove` for an agent | the verdict |
| 7 | Review | Should this land? | `scrutinize` | the verdict |
| 8 | Ship | Is there a way back? | `safe-release`, plus `agent-release` for an agent | the release note |
| 9 | Watch | Is it still right, and what did the last failure teach? | `agent-drift` for an agent; `safe-release`'s watch signals and `evolve-maintain`'s regression test otherwise | new eval tasks, regression tests |

Broken, slow or insecure work enters at its own skill (`debug-protocol`, `perf-optimize`,
`threat-model`) and rejoins at Build. `drive` walks these for you.

## The five flows

Every flow has the same shape: **find → change → prove → ship**.

| Goal | Find | Change | Prove | Ship |
|---|---|---|---|---|
| Build something new | `problem-framing` → `arch-design` → `plan-work` | `build-discipline` | `correctness-gate` | `safe-release` |
| Clean up a messy codebase | `arch-design` (audit) → `arch-map` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Fix a bug | `debug-protocol` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Make it faster or safer | `perf-optimize` / `threat-model` | same skill | `correctness-gate` | `safe-release` |
| Build an AI agent | `agent-design` → `agent-evals` (before any agent code) → `plan-work` | `build-discipline` | `agent-prove` | `safe-release` + `agent-release`, then `agent-drift` once it's live |

`drive` holds the same playbooks with its own steps; where the two disagree, `drive`'s wins.

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

Project memory: retrieve missing facts with `project-context`; after authorized changes use
`project-update` for affected records. Without helpers, follow/update existing notes directly;
read-only reviews report gaps. Skip upkeep when no durable fact changed.
