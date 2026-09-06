# Top-Tier Engineer

One folder that makes an AI coding agent behave like a top-tier engineer across the entire life of
a project — from a vague idea to a system maintained for years — regardless of which model is
running it.

## What's inside

```
top-tier-engineer/
├── README.md            ← you are here
├── PROTOCOL.md          ← the law: shared vocabulary, laws, ledgers, handoffs (stated once).
│                          §4 is the picture too: who consumes what, and who runs next.
│                          Rules only — every run loads this, so it stays lean.
├── CHANGELOG.md         ← versioned history; superseded behavior described, never erased
├── agents/              ← §6 parallel gates as isolated, artifacts-only subagents (fresh eyes, reproducible)
├── .claude-plugin/      ← manifest, so the folder installs as one Claude Code plugin
├── runs/                ← the run ledger: transcripts of real runs + the fixes they delivered.
│                          PROTOCOL cites these by name as the provenance of its rules.
│                          Published redacted — subjects are SUBJECT_A/B/C (see DECISION_LEDGER D004)
├── tools/
│   ├── structure-report.py ← the spaghetti alarm: structural shape + the debt ratchet (--baseline)
│   ├── structure_opacity.py← how much of a file a parser actually entered (§8, the denominator)
│   ├── graph-audit.py      ← the no-symptom sweep: dead modules, unused defs, layer-direction breaches (LATENT)
│   ├── test_tools.py       ← runs tools/tests/ (stdlib unittest, no deps)
│   └── tests/              ← one test module per tool
└── skills/
    ├── chief-engineer/      ← the router — every request enters here
    ├── problem-framing/     ← stage 1: falsifiable spec before any code
    ├── arch-design/         ← stage 2: reversible, recorded decisions
    ├── build-discipline/    ← stage 3: proven vertical slices
    ├── wire-check/          ← service: is it connected? (slice exit gate)
    ├── correctness-gate/    ← stage 4: is it provably right?
    ├── debug-protocol/      ← why is it wrong? (proven cause before any fix)
    ├── symptom-audit/       ← where does the felt complaint live? (trace → prescribe)
    ├── perf-optimize/       ← stage 5: measured, guarded improvement + the cost class of data access
    ├── threat-model/        ← what can an adversary make it do that it must not?
    ├── senior-review/       ← parallel gate: is it wise?
    ├── scrutinize/          ← parallel gate: should this change exist, does it do what it claims?
    ├── structure-gate/      ← service gate (also runs in CI): is it spaghetti, and did it get worse?
    ├── latent-audit/        ← no-symptom sweep: what is provably dead, mislayered, or dormantly broken?
    ├── data-evolution/      ← how does stored data change shape without loss, reversibly?
    ├── ship-gate/           ← is releasing it reversible, observable, bounded?
    ├── evolve-maintain/     ← stage 6: years-long health, incidents → invariants
    └── meta-skills/         ← always on: calibration, escalation, communication
```

## How to use it

You don't pick skills. You talk to the engineer:

- "I want an app that..." → routed through framing → design → build → gate
- "It's broken and I don't know why" → debug-protocol proves the cause, evolve-maintain fixes it
- "The app feels slow/clunky" → symptom-audit traces the complaint and prescribes a phased spec
- "Will this query scale / is this an N+1?" → perf-optimize's cost-class phase judges it from the execution plan, before a stopwatch exists
- "Is this secure / can this be abused?" → threat-model walks every trust boundary as an adversary
- "Is this code good?" → senior-review
- "Is this a mess / spaghetti / maintainable?" → structure-gate measures the structural shape (and is the gate CI runs unattended)
- "How did this file get to 4,000 lines when every commit looked fine?" → structure-gate's debt ratchet freezes accepted debt in `DEBT_LEDGER.md` so it cannot grow by defensible increments (§8)
- "Find dead code / are the layers respected?" (nothing feels wrong) → latent-audit sweeps the import graph for dead weight and layer breaches
- "Look at this PR / plan before it lands" → scrutinize
- "File the findings as issues / work through the backlog / implement issue #N" → chief-engineer carries the audits' findings out to your tracker intact (PROTOCOL §3), hands each back for implementation one at a time, and closes it only with evidence
- "Deploy it / ship it" → ship-gate proves it's reversible and bounded before it reaches users
- "Change the schema / run a migration" → data-evolution evolves the data shape without loss
- "Where are we?" → chief-engineer reads the project's ledgers and tells you the state and the next step
- "Every check passed and it still isn't what I meant / it's way too much for the job / I can't tell what it did" → the sense floor (§9): every report opens by quoting your own words back, saying what changed in your vocabulary, what you can now do, and what it cost you to have it

`chief-engineer` routes by **artifact state, not by your phrasing** — say "build it" with no brief
and it will (briefly, proportionally) frame first. Small tasks get the compressed lifecycle, never
bureaucracy. Slices that touch a trust boundary or persistent data never take the fast path,
regardless of size.

## Install

**Claude Code (plugin, recommended):** the folder ships its own local marketplace
(`.claude-plugin/marketplace.json`, marketplace name `thanaponai01-skills`). Register it, then
install the plugin:

```
/plugin marketplace add "E:\Me\5.Claude\01 ASSET\Skills\top-tier-engineer"
/plugin install top-tier-engineer@thanaponai01-skills
```

(Use the absolute path to wherever this folder lives.) Installed this way, the skills are
namespaced — `top-tier-engineer:chief-engineer`, `top-tier-engineer:senior-review`, etc. — so they
never collide with similarly named standalone skills, and the folder stays intact so every skill
can read `PROTOCOL.md` at the suite root.

**From GitHub (any machine):** the same marketplace lives in this repo, so on a machine with `gh`/git
authenticated to the account, install straight from GitHub:

```
/plugin marketplace add thanaponai01-collab/top-tier-engineer-skill
/plugin install top-tier-engineer@thanaponai01-skills
```

(The repo is private, so the machine must have access to it.)

**Fallback (loose skills):** copy each folder under `skills/` into `~/.claude/skills/` and keep
`PROTOCOL.md` at a stable path the skills can read (e.g. `~/.claude/skills/`). Note this
forfeits namespacing, so it will clash with any existing `senior-review` / `wire-check` skills.

**Cursor:** add the `SKILL.md` files as project rules, or paste `PROTOCOL.md` + the relevant
skill into context. Every skill degrades gracefully when used alone (see §1).

**Any other agent:** the files are plain markdown contracts — paste and go. Nothing here depends
on a vendor, a framework, or a model version. That is the point.

## Bootstrap a project (recommended)

Claude Code auto-reads a project's `CLAUDE.md` — it does not auto-read your ledgers or this suite.
Add this block to each governed project's `CLAUDE.md` so every fresh session lands wired:

```
This project is governed by the top-tier-engineer suite.
Route every substantial engineering request through the chief-engineer skill
(top-tier-engineer:chief-engineer) before acting.
Default to writing nothing to disk: the report is the deliverable (PROTOCOL §3).
Where this project does keep notes at the repo root, read them before writing anything.
If DEBT_LEDGER.md exists, check it before taking the "smallest diff" — a diff that
lands in a file listed there is a withdrawal, not a free move (§8).
```

## The history

Every version, what it superseded, and which real run earned it: `CHANGELOG.md`.
The runs themselves, with the fixes they delivered: `runs/`.

## The one-line summary

**Frame falsifiably, decide reversibly, build provably, verify connectedly, gate adversarially,
debug causally, audit symptomatically, optimize measurably, scale sub-linearly, defend
adversarially, ship reversibly, migrate losslessly, maintain memorably — and at every step, know
exactly how much you know.**
