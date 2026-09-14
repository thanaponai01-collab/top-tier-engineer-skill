# Top-Tier Engineer

Fourteen engineering skills for AI coding agents, plus one philosophy file. Skills say *what* to do
for a task; `PHILOSOPHY.md` says *how to work* on every task.

## Install (Claude Code)

```
git clone https://github.com/thanaponai01-collab/top-tier-engineer-skill
/plugin marketplace add <path-to-clone>
/plugin install top-tier-engineer@thanaponai01-skills
```

Then load the philosophy everywhere by adding one line to `~/.claude/CLAUDE.md`:

```
@<path-to-clone>/PHILOSOPHY.md
```

Claude picks the right skill from what you ask. You can also call one by name, e.g.
`/top-tier-engineer:debug-protocol`.

**Other agents:** every `skills/<name>/SKILL.md` is plain markdown. Copy the one you need and paste it.

## The skills

| Skill | Ask it |
|---|---|
| `problem-framing` | "I want an app that…": turns a vague idea into testable requirements |
| `arch-design` | "How should this be structured / which stack?" |
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

Skills don't hand off to each other; you pick the next one. Every flow has the same shape:
**find → change → prove → ship**.

| Goal | Find | Change | Prove | Ship |
|---|---|---|---|---|
| Build something new | `problem-framing` → `arch-design` | `build-discipline` | `correctness-gate` | `safe-release` |
| Improve a messy codebase | `arch-design` (audit) | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Fix a bug | `debug-protocol` | `evolve-maintain` | `correctness-gate` | `safe-release` |
| Make it faster | `perf-optimize` | `perf-optimize` | `correctness-gate` | `safe-release` |
| Make it secure | `threat-model` | `threat-model` | `correctness-gate` | `safe-release` |

Along the way:
- **Not sure where to start?** `senior-review` tells you the biggest gap, and so which flow.
- **Built but not working?** `wire-check`.
- **Want numbers or proof on a cleanup?** `structure-gate` for messy shape, `latent-audit` before
  deleting anything.
- **About to merge?** `scrutinize` for an outside opinion.

## Developing

```
python -m unittest discover tests
```
