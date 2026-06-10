# Top-Tier Engineer

One folder that makes an AI coding agent behave like a top-tier engineer across the entire life of
a project — from a vague idea to a system maintained for years — regardless of which model is
running it.

## What's inside

```
top-tier-engineer/
├── README.md            ← you are here
├── MAP.md               ← the picture: how the eleven skills connect
├── PROTOCOL.md          ← the law: shared vocabulary, laws, ledgers, handoffs (stated once)
├── .claude-plugin/      ← manifest, so the folder installs as one Claude Code plugin
└── skills/
    ├── chief-engineer/      ← NEW: the router — every request enters here
    ├── problem-framing/     ← stage 1: falsifiable spec before any code
    ├── arch-design/         ← stage 2: reversible, recorded decisions
    ├── build-discipline/    ← stage 3: proven vertical slices
    ├── wire-check/          ← service: is it connected? (slice exit gate)
    ├── correctness-gate/    ← stage 4: is it provably right?
    ├── debug-protocol/      ← NEW: why is it wrong? (proven cause before any fix)
    ├── perf-optimize/       ← stage 5: measured, guarded improvement
    ├── senior-review/       ← parallel gate: is it wise?
    ├── evolve-maintain/     ← stage 6: years-long health, incidents → invariants
    └── meta-skills/         ← always on: calibration, escalation, communication
```

## How to use it

You don't pick skills. You talk to the engineer:

- "I want an app that..." → routed through framing → design → build → gate
- "It's broken and I don't know why" → debug-protocol proves the cause, evolve-maintain fixes it
- "Is this code good?" → senior-review
- "Where are we?" → chief-engineer reads the project's ledgers and tells you the state and the next step

`chief-engineer` routes by **artifact state, not by your phrasing** — say "build it" with no brief
and it will (briefly, proportionally) frame first. Small tasks get the compressed lifecycle, never
bureaucracy.

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
can read `PROTOCOL.md` + `MAP.md` at the suite root.

**From GitHub (any machine):** the same marketplace lives in this repo, so on a machine with `gh`/git
authenticated to the account, install straight from GitHub:

```
/plugin marketplace add thanaponai01-collab/top-tier-engineer-skill
/plugin install top-tier-engineer@thanaponai01-skills
```

(The repo is private, so the machine must have access to it.)

**Fallback (loose skills):** copy each folder under `skills/` into `~/.claude/skills/` and keep
`PROTOCOL.md` + `MAP.md` at a stable path the skills can read (e.g. `~/.claude/skills/`). Note this
forfeits namespacing, so it will clash with any existing `senior-review` / `wire-check` skills.

**Cursor:** add the `SKILL.md` files as project rules, or paste `PROTOCOL.md` + the relevant
skill into context. Every skill degrades gracefully when used alone (see PROTOCOL §6).

**Any other agent:** the files are plain markdown contracts — paste and go. Nothing here depends
on a vendor, a framework, or a model version. That is the point.

## Design decisions made while wiring (the diagnosis behind this artifact)

1. **Vocabulary was duplicated and had drifted.** Every skill restated the evidence tags, and
   `senior-review` had drifted to **(traced)** where the suite standard is **(trace-only)** — a
   violation of Law 1 ("every rule lives in exactly one place"). Fix: `PROTOCOL.md` is now the
   single authority; skills carry a one-line gloss only for standalone survival (PROTOCOL §6), and
   senior-review is conformed. **(suspected)** was promoted into the shared vocabulary as the
   fourth tier — it was useful in senior-review and is now legal everywhere.
2. **Nothing routed.** Ten contracts with no dispatcher means the user does the wiring by hand.
   Fix: `chief-engineer`, which routes by artifact census (what ledgers exist) rather than by the
   verb in the request — the most common routing error is taking "fix it" or "build it" literally.
3. **A mandate was missing.** wire-check owns "is it connected?", correctness-gate owns "is it
   right?", senior-review owns "is it wise?" — nobody owned **"why is it wrong?"**. Fix:
   `debug-protocol` (reproduce → stabilize → bisect → hypothesize → two-way proof), which ends at
   a proven cause and hands the fix to evolve-maintain. Its two-way test (cause present →
   failure reproduces; cause removed → failure gone) is what separates a found cause from a
   hidden symptom.
4. **Every skill now carries a Wiring block** — consumes / produces / upstream / downstream —
   stated once at the top, so each handoff has exactly one authoritative description and a future
   model can walk the chain from any file it lands in.
5. **Every skill now ends in a machine-parseable verdict line** (wire-check and senior-review
   gained theirs) so a transcript or log shows where the lifecycle stopped, greppably.
6. **One thing deliberately NOT added** (anti-scope): no security-audit, release-management, or
   data-migration skills. Security lives inside senior-review's "Safety & trust" dimension and
   correctness-gate's hostile tests; releases are a passed gate + review; adding skills that
   overlap existing mandates would violate Law 1. Add a new skill only when a question has no
   owner — that was debug-protocol's bar, and it should be the next one's too.

## The one-line summary

**Frame falsifiably, decide reversibly, build provably, verify connectedly, gate adversarially,
debug causally, optimize measurably, maintain memorably — and at every step, know exactly how
much you know.**
