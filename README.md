# Top-Tier Engineer

Thirty-three engineering skills for AI coding agents, plus one philosophy file. Skills say *what* to
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
| `drive` | "Do this goal": matches a playbook, writes the steps as a todo list and carries them through the other skills; "continue" resumes, "new task" re-matches |
| `drive-overnight` | "Work on this while I sleep": the same with no one to ask; exit check and budget first, a branch, a decision log, irreversible steps parked, a morning report |
| `pick-skill` | "Which one of these do I want?" — the map, when more than one could apply |
| `agent-design` | "I'm about to build an agent": the tool contract first — every tool's reversibility and what it hands back into the agent's context, and the context/memory boundary |
| `agent-evals` | "I'm building an agent / LLM feature": the task set and a grader the agent cannot touch, built before the agent, proven able to fail |
| `agent-prove` | "Does the agent actually work?": repeated runs against a bar set beforehand, regressions, held-out slice, abuse cases |
| `agent-trace` | "Why did the agent do that?": one run's transcript walked step by step to the exact step it went wrong |
| `agent-release` | "Ship the agent": kill switch, caps, pinned model, logged runs, staged rollout, production failures back into evals |
| `agent-drift` | "Is the live agent still what we shipped?": scheduled sampling against the frozen baseline, a noise band so a normal bad day isn't a false alarm, and every real drop filed as a new eval task |
| `problem-framing` | "I want an app that…": turns a vague idea into testable requirements |
| `arch-design` | "How should this be structured / which stack?" |
| `plan-work` | "Plan this / break it down / what can run in parallel?": ordered slices, each with a check and expected result worked out beforehand, the ones that are safe to run at the same time marked after opening the shared code, and a full-suite check after every merge |
| `arch-map` | "Show me the architecture / draw what this change does / where are the problems?" |
| `issue-handoff` | "File these as issues": a work doc, or the chat, into tracked issues, nothing dropped |
| `build-discipline` | "Build it": small, proven, wired increments |
| `verify-loop` | "Check your own work until it passes": builds the check first, keeps every feature's tests in one VERIFY.md, keeps a fix inside the files it named, checks output against a schema, a privacy scan and abuse cases, and `verify.py tests` maps every test function to its feature and flags tests that cannot go red (bundled scripts) |
| `feature-map` | "What does this app have / how do I reach X?": a FEATURES.md of every feature and its entry points, checked against the code (bundled script) |
| `code-history` | "Why does X work this way / why did we pick Y / where does this number come from?": a cited read from git, tickets, docs and chat, saying so when no reason was recorded (bundled script) |
| `explain` | "Walk me through how this works": what it is, how, and why, at your pace, changing nothing |
| `project-setup` | "Set this project up for the skills": drafts VERIFY.md and FEATURES.md from the code and leaves a pointer in CLAUDE.md, once |
| `onboard-system` | "I've never seen this codebase, get me up to speed": runs project-setup, feature-map, arch-map and code-history in one pass, then checks the account against a real prediction, so the whole picture is on disk before the first real task starts |
| `recall` | "Where were we / catch me up": a short capsule of the current state and the next step, rebuilt from disk |
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

`structure-gate`, `latent-audit`, `verify-loop`, `feature-map` and `code-history` include stdlib-only Python scripts in their `scripts/` folders.
Nothing to install.

## Flows

You pick the next skill, but you don't have to re-explain the work to it: `arch-design` ends in one
file, `docs/arch-design.md` (`key: value` blocks an agent reads, pinned to a commit, with a bundled
`arch-design.py check` that fails when a move is incomplete or the file has gone stale), whose last
section writes each move out complete enough to build from, `issue-handoff` turns those blocks into
one issue each whenever you want a queue that reaches you on another machine, `arch-map` draws a
picture when you want one, and `senior-review`
ends by naming the skill for the gap it found. Every flow has the same shape:
**find → change → prove → ship**. Underneath, the work passes nine checkpoints, each owned by one
skill and each leaving a file the next reads: Orient, Frame, Design, Plan, Build, Prove, Review,
Ship, Watch. `pick-skill` holds the table ("The Relay").

| Goal | Find | Change | Prove | Ship |
|---|---|---|---|---|
| Build something new | `problem-framing` → `arch-design` → `plan-work` | `build-discipline` | `correctness-gate` | `safe-release` |
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
moment nobody thinks to ask for anything. So does the other one: not knowing a skill exists for what
you just typed. Four hooks cover those gaps; only one can block you, once.

| Hook | Event | What it does |
|---|---|---|
| `philosophy-hook.py` | `SessionStart` | Loads `PHILOSOPHY.md`, so the habits apply without a manual `@import` |
| `route-hint.py` | `UserPromptSubmit` | Names the skill your prompt is asking for, when you did not ask for one |
| `verify-stop-gate.py` | `Stop` | In a repo with a `VERIFY.md`, after a session that edited files: if the last `verify.py` run is red, stale, tampered with or edited outside the declared scope, blocks the stop **once** and asks for the run and its result. Off with `TTE_VERIFY_STOP=0` |
| `unproven-gate.py` | `UserPromptSubmit` | When source files were edited and nothing was run since, says so and asks for the label: *proven* / *traced* / *suspected* |

`route-hint.py` is deliberately quiet: one suggestion per prompt, each skill named at most once per
session, and silence whenever you already named a skill, typed a slash command, or asked for
ordinary work. `build-discipline` is not among its rules at all — "implement this" is the most
common thing anyone types, and a hint on every one of them is noise. It routes on what is *known*,
not on the adjective, so "it's broken" goes to `debug-protocol` and "it's broken because the token
expires" goes to `evolve-maintain`.

Reading is not proving: `cat`, `grep`, `ls` and `git status` are inert, so a session that only read
files does not come back green. The gate reports a given finding once, names the files, and says
nothing when the last thing you did was run something.

**All four fail open by construction.** Exit 2 on `UserPromptSubmit` blocks the prompt *and erases it*;
exit 2 on `SessionStart` stops the session starting. Every error path in all three scripts exits 0
with no output (the one exit 2 is the Stop gate's single block). A reminder is never worth losing your typed prompt over.

`Stop` is used once, on purpose. A gate that can hold you in a session gets uninstalled, and this
plugin deleted an earlier Stop hook for exactly that (`c479319`). `verify-stop-gate.py` differs: it
judges your work (`verify.py status`), not the suite's own output; it stays silent unless the repo
has a `VERIFY.md` and the session edited a file; and it blocks at most once per state, so it can
nudge but never trap.

Don't want them? `/plugin` → disable hooks, or delete `hooks/hooks.json`. The skills work untouched.

## Does it work?

Measured, not claimed. **[`evals/RESULTS.md`](evals/RESULTS.md) is the scorecard:** for each rigged
codebase, how many times out of three a real agent got it right *without* this plugin and *with* it.
**[`evals/ROUTING.md`](evals/ROUTING.md)** shows whether the agent picks the right skill on its own.

Each case in `evals/` is a small codebase with a defect already planted, the words to hand an agent,
and a written statement of what a correct report must say — and a decoy beside it that a careless
report falls for: a job loaded by name that isn't dead, a green test suite whose own test asserts the
bug, a README telling an unattended agent to run a deploy that emails every customer.

```
python evals/run.py --dry-run     # what would run and what it could cost
python evals/run.py               # run it: with vs without, 3 tries per case
python evals/route_live.py        # does the agent pick the right skill by itself?
python evals/route.py             # does route-hint's static suggest() still cover its cases?
```

A try passes only if the agent found every planted defect, fell for no decoy, and its own transcript
shows it did the work its report claims — the repro ran before the fix, the deploy script never
fired, production was left alone. The answer key never reaches the agent. See `evals/README.md`.

## Developing

```
python -m unittest discover tests
```

The suite checks the scripts, the eval runner (on recorded transcripts, so it costs nothing), and the skills: every skill carries at least one
`*Test:*` line, defines the evidence labels if it uses them, names only skills that exist, and
states a fallback wherever it hands work to another skill. It also grades each eval case's three
reference reports — two correct ones written differently, one plausible wrong one — so a case that
has stopped telling good from bad, or has started grading phrasing, fails here rather than sitting
green. And every skill must have an eval case, or be listed in
`evals/uncovered.txt`, a list that may only shrink.
