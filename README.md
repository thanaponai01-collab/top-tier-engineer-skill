# Top-Tier Engineer

Thirty-three engineering skills for AI coding agents, plus one philosophy file. Skills say *what* to
do for a task; `PHILOSOPHY.md` offers optional engineering guidelines.

Each skill is written to survive on its own: it defines any notation it uses, and where it hands
work to another skill it also says what to do when that skill isn't there. `evals/` holds the
rigged codebases that check whether the skills actually find what they claim to find.

## Install (Claude Code)

```
git clone https://github.com/thanaponai01-collab/top-tier-engineer-skill
/plugin marketplace add <path-to-clone>
/plugin install top-tier-engineer@thanaponai01-skills
```

That is the whole install. No hooks run by default, and no philosophy or workflow is
injected into the session. Skills are available when useful; ordinary work can proceed directly.

Use `/top-tier-engineer:drive` with a goal when you want the full workflow. It chooses and runs
the relevant skills, so you do not need to invoke each one. You can also call an individual
skill by name, e.g. `/top-tier-engineer:debug-protocol`. Skipping a skill needs no justification.

**Starting in a project:** no manual seed is required. Give the task and its expected result;
the agent discovers existing commands, entry points and tests, then verifies the relevant behavior.
`verify-loop` saves a small reusable recipe in VERIFY.md and grows it as needed. A complete
FEATURES.md map is optional; `project-setup` is available when you want those starter files upfront.
The map records what was found, while executed checks establish what worked.

**Other agents:** every `skills/<name>/SKILL.md` is plain markdown. Copy the one you need and
paste it — it carries its own vocabulary and its own fallbacks, so nothing silently depends on
the rest of this repo being loaded.

## The skills

| Skill | Ask it |
|---|---|
| `drive` | "Do this goal": matches a playbook, pins a run contract and advances on executed evidence; resumes uncertain actions safely and carries authorized releases through observation |
| `drive-overnight` | "Work on this while I sleep": the same with no one to ask; scoped authority and budgets first, a branch, decisions recorded, out-of-scope actions parked, a morning report |
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
| `build-discipline` | "Build it": small, proven, wired increments; reusable recipes finish with verify-loop evidence while BUILD.md retains slice progress |
| `verify-loop` | "Check your own work until it passes": discovers a project recipe without manual setup, records a real failed check before trusting a strict pass, keeps reusable checks in VERIFY.md, and flags stale evidence, changed oracles and unmapped tests (bundled scripts) |
| `feature-map` | "What does this app have / how do I reach X?": a FEATURES.md of every feature and its entry points, checked against the code (bundled script) |
| `code-history` | "Why does X work this way / why did we pick Y / where does this number come from?": a cited read from git, tickets, docs and chat, saying so when no reason was recorded (bundled script) |
| `explain` | "Walk me through how this works": what it is, how, and why, at your pace, changing nothing |
| `project-setup` | "Set this project up for the skills": discovers native commands, refreshes a small verification seed, preserves manual notes and proves local readiness; optional CI setup |
| `onboard-system` | "I've never seen this codebase, get me up to speed": runs project-setup, feature-map, arch-map and code-history in one pass, then checks the account against a real prediction, so the whole picture is on disk before the first real task starts |
| `recall` | "Where were we / catch me up": a short capsule of the current state and the next step, rebuilt from disk |
| `wire-check` | "I built it but it isn't working / is this hooked up? / what does nothing call?" |
| `correctness-gate` | "Does this actually work? Test it." |
| `debug-protocol` | "It's broken and I don't know why": proves the cause; an authorized fix carries the reproduction into reusable regression verification |
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

`drive` also includes a stdlib-only evidence controller. For a multi-step goal, RUN.json owns the
contract, stage evidence, attempts and external action journal. See its
[run contract](skills/drive/references/run-contract.md): `init`, `next`, `check`, `begin`, `reconcile`,
`finish`, `status`, and honest `stop blocked|failed`. Supporting build and release notes hold detail.
An interrupted deploy is reconciled against the provider before retrying; finish reruns checks,
never mutations. Staging and production goals end in version/journey checks and bounded observation.

The promise is a verified result in the requested environment **or an explicit blocked/failed
handoff with preserved work**. The helper is not a scheduler or security sandbox. Protect independent
acceptance checks in CI and restrict host tools/credentials; local writable hashes cannot enforce
permissions against their writer. Other agents can use the helper directly and put `status` in
their completion gate; the optional Stop integration below is for Claude Code.

## Flows

You pick the next skill, but you don't have to re-explain the work to it: `arch-design` ends in one
file, `docs/arch-design.md` (`key: value` blocks an agent reads, pinned to a commit, with a bundled
`arch-design.py check` that fails when a move is incomplete or the file has gone stale), whose last
section writes each move out complete enough to build from, `issue-handoff` turns those blocks into
one issue each whenever you want a queue that reaches you on another machine, `arch-map` draws a
picture when you want one, and `senior-review`
ends by naming the skill for the gap it found. Every flow has the same shape:
**find → change → prove → ship**. For a full workflow, the map offers nine checkpoints, each owned by one
skill with a file the next can read: Orient, Frame, Design, Plan, Build, Prove, Review,
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

## Context that outlives the session

A new session knows only what it can read, so the skills keep a project's memory in a few files,
in three layers:

| Layer | Read | Budget | Files |
|---|---|---|---|
| Always loaded | every session, by Claude Code itself | 30 lines | the start-here block in `CLAUDE.md` / `AGENTS.md` (`project-setup`) |
| Read at start | when work begins | 120 / 80 lines | `BRIEF.md`: the goal and `## Decisions` in force (`problem-framing`); `BUILD.md`: proven slices and `## Next` (`build-discipline`) |
| On demand | when a task touches it | per file | `FEATURES.md` / `VERIFY.md` areas via `include:`, `WHY.md` entries, every `*.archive.md` |

A decision said in chat, even in passing, is written to `BRIEF.md` before the work that acts on it;
one that overrides another replaces its line, and the old line moves to `BRIEF.archive.md`. Notes grow
by sending old detail down a layer, never by getting longer at the top. `recall`'s
`scripts/context_budget.py` names every note over budget and the move that fixes it; `/recall`
rebuilds where things stand from all of it.

## Hooks

The default `hooks/hooks.json` has no active hooks. Installing the plugin does not route
prompts, inject instructions, or block the agent from ending a turn. `drive` works without hooks.

For one-prompt runs nobody watches, copy `hooks/autonomous.json` instead (philosophy and the project's decisions at start, `drive` loaded first, one stop-block on a red verify run). If you explicitly want the hooks, copy `hooks/optional.json` over `hooks/hooks.json` in your
plugin checkout and reload the plugin. To return to the default, restore `hooks/hooks.json`
to `{"hooks": {}}`. Hook configuration is separate from choosing `drive`.

| Optional hook | Event | What it does |
|---|---|---|
| `philosophy-hook.py` | `SessionStart` | Loads the optional engineering guidelines in `PHILOSOPHY.md` |
| `start-here-hook.py` | `SessionStart` | Hands the session the project's `## Decisions` (BRIEF.md) and `## Next` (BUILD.md), and names any note over its line budget; silent when there are none |
| `drive-entry.py` | `UserPromptSubmit` | Autonomous profile only (`hooks/autonomous.json`): on a task-shaped prompt, tells the agent to load `drive` before any other tool call |
| `route-hint.py` | `UserPromptSubmit` | Suggests a relevant skill; using it is optional and skipping it needs no justification |
| `unproven-gate.py` | `UserPromptSubmit` | Reminds the agent when source files changed without anything being run since |
| `verify-stop-gate.py` | `Stop` | With RUN.json: repeatedly blocks incomplete, invalid or stale completion, including resumed sessions; allows passing evidence or an explicit blocked/failed handoff. Without RUN.json: retains the one-time VERIFY.md reminder after edits. Off with `TTE_VERIFY_STOP=0` |

Prompt/session hooks fail open. The optional Stop hook checks RUN.json strictly when present,
allowing successful evidence or an explicit failed/blocked handoff. Without RUN.json it retains the
one-time VERIFY.md reminder. Hooks remain opt-in; invoking drive does not enable them.

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
