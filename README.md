# Top-Tier Engineer

Thirteen engineering skills for AI coding agents. Each one works on its own: install and go, no setup,
no config, no router.

## Install (Claude Code)

```
/plugin marketplace add thanaponai01-collab/top-tier-engineer-skill
/plugin install top-tier-engineer@thanaponai01-skills
```

Or from a local copy: `/plugin marketplace add <path-to-this-folder>`, then the same install line.

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
| `senior-review` | "Is this code good?", "second opinion on this PR", "what's the biggest gap?" |
| `structure-gate` | "Is this spaghetti?" (bundled script) |
| `latent-audit` | "Find dead code / are the layers respected?" (bundled script) |
| `safe-release` | "Ship it", "run this migration" |
| `evolve-maintain` | "Fix / upgrade / refactor / deprecate on a running system" |

`structure-gate` and `latent-audit` include stdlib-only Python scripts in their `scripts/` folders.
Nothing to install.

## Developing

```
python -m unittest discover tests
```
