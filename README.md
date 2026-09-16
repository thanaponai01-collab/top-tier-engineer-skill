# Top-Tier Engineer

Seventeen engineering skills for AI coding agents, plus one philosophy file. Skills say *what* to
do for a task; `PHILOSOPHY.md` says *how to work* on every task.

Each skill is written to survive on its own: it defines any notation it uses, and where it hands
work to another skill it also says what to do when that skill isn't there. `evals/` holds the
rigged codebases that check whether the skills actually find what they claim to find.

## Install (Claude Code)

```
git clone https://github.com/thanaponai01-collab/top-tier-engineer-skill
/plugin marketplace add <path-to-clone>
/plugin install top-tier-engineer@thanaponai01-skills
```

That is the whole install. `PHILOSOPHY.md` loads itself at session start, and the unproven-change
gate runs from the same manifest — see [Hooks](#hooks).

Claude picks the right skill from what you ask. You can also call one by name, e.g.
`/top-tier-engineer:debug-protocol`.

**Other agents:** every `skills/<name>/SKILL.md` is plain markdown. Copy the one you need and
paste it — it carries its own vocabulary and its own fallbacks, so nothing silently depends on
the rest of this repo being loaded.

## The skills

| Skill | Ask it |
|---|---|
| `pick-skill` | "Which one of these do I want?" — the map, when more than one could apply |
| `problem-framing` | "I want an app that…": turns a vague idea into testable requirements |
| `arch-design` | "How should this be structured / which stack?" |
| `arch-map` | "Show me the architecture / draw what this change does / where are the problems?" |
| `issue-handoff` | "File these as issues": a work doc, or the chat, into tracked issues, nothing dropped |
| `build-discipline` | "Build it": small, proven, wired increments |
| `wire-check` | "I built it but it isn't working / is this hooked up? / what does nothing call?" |
| `correctness-gate` | "Does this actually work? Test it." |
| `debug-protocol` | "It's broken and I don't know why" |
| `perf-optimize` | "It's slow / feels clunky / will this query scale?" |
| `threat-model` | "Is this secure / can it be abused?" |
| `senior-review` | "Is this code good?", "what's the biggest gap?" |
| `scrutinize` | "Second opinion on this PR / plan" |
| `structure-gate` | "Is this spaghetti?" (bundled script) |
| `latent-audit` | "Find dead code / are the layers respected?" (bundled script) |
| `safe-release` | "Ship it", "run this migration" |
| `evolve-maintain` | "Fix / upgrade / refactor / deprecate on a running system" |

`structure-gate` and `latent-audit` include stdlib-only Python scripts in their `scripts/` folders.
Nothing to install.

## Flows

You pick the next skill, but you don't have to re-explain the work to it: `arch-design` ends in one
file, `docs/arch-design.md`, whose last section writes each move out as a block complete enough to
build from, `issue-handoff` turns those blocks into one issue each whenever you want a queue that
reaches you on another machine, `arch-map` draws and writes that file — and every map it draws — from
the findings handed over, and `senior-review`
ends by naming the skill for the gap it found. Every flow has the same shape:
**find → change → prove → ship**.

| Goal | Find | Change | Prove | Ship |
|---|---|---|---|---|
| Build something new | `problem-framing` → `arch-design` | `build-discipline` | `correctness-gate` | `safe-release` |
| Improve a messy codebase | `arch-design` (audit) → `arch-map` (problems) | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Fix a bug | `debug-protocol` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Make it faster | `perf-optimize` | `perf-optimize` | `correctness-gate` | `safe-release` |
| Make it secure | `threat-model` | `threat-model` | `correctness-gate` | `safe-release` |

Along the way:
- **Not sure which skill?** `pick-skill` routes it in one decision, including the five that all
  sound like "review my code".
- **Not sure what's wrong at all?** `senior-review` tells you the biggest gap, and so which flow.
- **Want to see it?** `arch-map` draws the structure, a change's before → after, or where the problems sit.
- **Built but not working?** `wire-check`.
- **Want numbers or proof on a cleanup?** `structure-gate` for messy shape, `latent-audit` before
  deleting anything.
- **Work out of sight — written down, or only said?** `issue-handoff` files a planned-work doc, or
  the conversation itself, as issues, verbatim, so it reaches you from any machine.
- **About to merge?** `scrutinize` for an outside opinion.

## Hooks

Every skill here is *pull*: it runs because you asked for it. The failure they are all written
against — code changed, turn ended, "it should work" standing in for a result — happens at the
moment nobody thinks to ask for anything. Two hooks cover that gap, and neither can block you.

| Hook | Event | What it does |
|---|---|---|
| `philosophy-hook.py` | `SessionStart` | Loads `PHILOSOPHY.md`, so the habits apply without a manual `@import` |
| `unproven-gate.py` | `UserPromptSubmit` | When source files were edited and nothing was run since, says so and asks for the label: *proven* / *traced* / *suspected* |

Reading is not proving: `cat`, `grep`, `ls` and `git status` are inert, so a session that only read
files does not come back green. The gate reports a given finding once, names the files, and says
nothing when the last thing you did was run something.

**Both fail open by construction.** Exit 2 on `UserPromptSubmit` blocks the prompt *and erases it*;
exit 2 on `SessionStart` stops the session starting. Every error path in both scripts exits 0 with
no output. A reminder is never worth losing your typed prompt over.

Not on `Stop`, deliberately: reaching the model from `Stop` means `decision: "block"`, and a gate
that can hold you in a session you asked to leave gets uninstalled — after which it protects nobody.
This plugin shipped a Stop hook once and deleted it for exactly that (`c479319`).

Don't want them? `/plugin` → disable hooks, or delete `hooks/hooks.json`. The skills work untouched.

## Does it work?

`evals/` answers that. Each case is a small codebase with a defect already planted, the words to
hand an agent, and a written statement of what a correct report must say — and a decoy beside it
that a careless report falls for: a job loaded by name that isn't dead, a green test suite whose
own test asserts the bug, a file that reads as clean because no parser could enter it.

```
python evals/grade.py --list
python evals/grade.py <case> --report path/to/report.md
```

Missing a finding lowers the score. Falling for a decoy fails the case outright, at any score.
See `evals/README.md`.

## Developing

```
python -m unittest discover tests
```

The suite checks the scripts, and it checks the skills: every skill carries at least one
`*Test:*` line, defines the evidence labels if it uses them, names only skills that exist, and
states a fallback wherever it hands work to another skill. It also grades each eval case's two
reference reports, so a case that has stopped telling good from bad fails here rather than
sitting green.
