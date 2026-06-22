# Top-Tier Engineer

One folder that makes an AI coding agent behave like a top-tier engineer across the entire life of
a project — from a vague idea to a system maintained for years — regardless of which model is
running it.

## Proven in practice

This suite is not just designed; it has been run against real code, twice, and the runs are
recorded honestly (see `LIVE_RUN_001.md`, `LIVE_RUN_002.md`):

- **Run 1 — a ~1,700-LOC Flask/SQLite ticket app.** Seven findings, **all proven by executing the
  real code**: a full admin-auth bypass, reversibly-stored passwords, overbooking past capacity (a
  bad guard *and* a race), and two schema/lookup defects. Fixes shipped.
- **Run 2 — an 18,300-LOC agent-memory system** (asyncio daemon, SQLite+HNSW, hybrid retrieval).
  One **proven** N+1 on the hot retrieval path, found by `data-tier`. One concurrency hypothesis
  **disproved** by its own two-way test and correctly refused as a finding. Two clean checks.

The second run's disproved hypothesis matters as much as the findings: the suite's evidence rules
forbid a plausible-but-unproven concern from ever wearing a verdict's costume. That is the whole
point — *know exactly how much you know.*

## What's inside

```
top-tier-engineer/
├── README.md            ← you are here
├── MAP.md               ← the picture: how the seventeen skills connect
├── PROTOCOL.md          ← the law: shared vocabulary, laws, ledgers, handoffs (stated once)
├── CHANGELOG.md         ← versioned history; superseded behavior described, never erased
├── LIVE_RUN_001.md      ← first real execution (Flask ticket app): 7 proven findings
├── LIVE_RUN_002.md      ← second real execution (18k-LOC memory system): 1 proven, 1 disproved
├── .claude-plugin/      ← manifest, so the folder installs as one Claude Code plugin
├── tools/
│   └── verdict-lint.py  ← mechanical enforcement: validates verdict-line form (PROTOCOL §5)
└── skills/
    ├── chief-engineer/      ← the router — every request enters here
    ├── problem-framing/     ← stage 1: falsifiable spec before any code
    ├── arch-design/         ← stage 2: reversible, recorded decisions
    ├── build-discipline/    ← stage 3: proven vertical slices
    ├── wire-check/          ← service: is it connected? (slice exit gate)
    ├── correctness-gate/    ← stage 4: is it provably right?
    ├── debug-protocol/      ← why is it wrong? (proven cause before any fix)
    ├── symptom-audit/       ← where does the felt complaint live? (trace → prescribe)
    ├── perf-optimize/       ← stage 5: measured, guarded improvement
    ├── data-tier/           ← does this query scale better than the data grows? (cost class)
    ├── threat-model/        ← what can an adversary make it do that it must not?
    ├── senior-review/       ← parallel gate: is it wise?
    ├── scrutinize/          ← parallel gate: should this change exist, does it do what it claims?
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
- "Will this query scale / is this an N+1?" → data-tier judges cost class from the execution plan
- "Is this secure / can this be abused?" → threat-model walks every trust boundary as an adversary
- "Is this code good?" → senior-review
- "Look at this PR / plan before it lands" → scrutinize
- "Deploy it / ship it" → ship-gate proves it's reversible and bounded before it reaches users
- "Change the schema / run a migration" → data-evolution evolves the data shape without loss
- "Where are we?" → chief-engineer reads the project's ledgers and tells you the state and the next step

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

## Bootstrap a project (recommended)

Claude Code auto-reads a project's `CLAUDE.md` — it does not auto-read your ledgers or this suite.
Add this block to each governed project's `CLAUDE.md` so every fresh session lands wired:

```
This project is governed by the top-tier-engineer suite.
Route every substantial engineering request through the chief-engineer skill
(top-tier-engineer:chief-engineer) before acting.
Project memory lives in the ledgers at the repo root (PROBLEM_BRIEF.md, ASSUMPTIONS.md,
ARCHITECTURE.md, DECISION_LEDGER.md, TODO_LEDGER.md, CORRECTNESS_VERDICT.md, PERF_BUDGET.md,
DATA_TIER.md, AUDIT_SPEC.md, THREAT_MODEL.md, REVIEW_LEDGER.md, MIGRATION_PLAN.md,
RELEASE_PLAN.md, MAINT_LOG.md) — read the ones that exist before writing anything.
```

## The history (diagnosis, decisions, and what real runs proved)

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
6. **The suite assumed its own wiring.** "Read PROTOCOL.md at the suite root" never said *where*
   the root is from inside an installed plugin, and "invoke skill X" never said what invoking
   means when skills are files, not functions. The suite failed its own wire-check: its links
   existed but were not Routed. Fix: PROTOCOL §0 (resolution order + invocation semantics),
   chief-engineer Phase 0, and the CLAUDE.md bootstrap block above.
7. **Scaling down was a promise, not a mechanism.** "Lightweight by default" had no definition, so
   a thirty-line script could legally spawn nine ledger files. Fix: the scale rule (PROTOCOL §7 —
   ledgers materialize as files only when memory must outlive the session, else inline) and the
   concrete fast path in chief-engineer. The escape hatch is now also explicit: questions and
   explanations route to no lifecycle skill at all, and requests with no owning mandate are named
   as such instead of stretched into one.
8. **Rigor without taste was a ceiling.** v1.2 adds the judgment layer great engineers carry:
   simplicity as a discipline with teeth (the subtraction pass, meta-skills D7), a dependency
   adoption bar (arch-design), a legal throwaway mode so prototyping never has to break discipline
   (spike mode, chief-engineer), mandatory diff self-review before any commit (the short leash,
   build-discipline), and direct inspection of real outputs alongside assertions
   (correctness-gate). Process keeps you safe; these keep you sharp.
9. **A twelfth skill passed the bar.** `scrutinize` (adapted from an external skill) owns the
   delta — a plan, PR, diff, or design doc that hasn't landed — asking "should this change exist,
   and does it do what it claims?" Nobody owned that: senior-review judges codebases and mentors
   authors; correctness-gate proves built systems. Adapting it meant conforming it to suite law:
   a Wiring block (it was an orphan — ironic for an end-to-end reviewer), evidence tags replacing
   its informal claim-vs-verification rule, its simpler-alternative pass becoming the
   operationalization of Discipline 7 rather than a second statement of it, a Law 3 guard on its
   outsider stance (plus a ledger check, so explained surprises read as archaeology, not signal),
   a registry verdict line, and a clean trigger boundary against senior-review.
10. **A thirteenth skill passed the bar.** `symptom-audit` (distilled from a real audit run, then
   abstracted) owns the previously unowned question **"where does a felt complaint live in an
   existing codebase, and what's the cheapest ranked path to relief?"** Nobody owned it:
   perf-optimize *forbids* this mode (it requires a runnable, gated system and a profiler, and
   bans trace-only results); debug-protocol owns broken, not slow-but-working; senior-review is
   whole-codebase, not symptom-scoped. Conforming it to suite law meant: its evidence rule became
   a pointer to the PROTOCOL vocabulary (its findings honestly cap at (trace-only) — only
   perf-optimize may claim a measured gain); its "Verify" phase became *Pre-verify* — it
   pre-writes the checks that perf-optimize/correctness-gate execute, never claiming them itself;
   its rewrite escalation routes through arch-design; its swappable sweep checklist is named as
   the only audit-type-specific part; ledger `AUDIT_SPEC.md`, verdict noun `AUDIT:`, routing rows
   in chief-engineer split cleanly against perf-optimize.
11. **The first real run changed everything (v1.5.0).** v1.3.1 flagged the suite's #1 risk: every
   claim that it *worked* was (trace-only) until a real project ran the full lifecycle.
   `LIVE_RUN_001` is that run — the suite executed against a real ~1,700-LOC Flask/SQLite ticket
   app and produced **seven findings, all (proven) by executing the real code**: a forgeable admin
   token (full auth bypass), reversibly-encrypted passwords, overbooking past venue capacity (a
   guard that ignored the requested count *and* a TOCTOU race), a `unique=True` on a quantity
   column, and OR-filter lookups returning unrelated rows. The lifecycle is now proven on foreign
   code, not just on its own design.
12. **Three skills the first run justified (v1.5.0).** Four findings had no owning skill with a real
   *pipeline* — they were caught only as `senior-review` checkboxes. A dimension that *catches* a
   finding is not a skill that *owns* the method, so: `threat-model` (adversarial security: assets →
   trust boundaries → abuse-case tests handed to the gate), `ship-gate` (the previously unowned act
   of shipping: reversibility, blast radius, rollback), and `data-evolution` (data-shape change,
   whose rollback semantics differ from code's — `git revert` restores code, not dropped columns).
   This **supersedes the earlier anti-scope decision** that folded security and releases into
   existing dimensions: evidence showed a dimension was not enough.
13. **First mechanical enforcement (v1.5.0).** The suite's standing residual risk was "exhortation
   without enforcement." `tools/verdict-lint.py` parses verdict lines from a transcript/PR/log and
   checks PROTOCOL §5 *form* — unregistered nouns, illegal states, trace-only verdicts missing the
   required bold limitation marker, success/failure contradictions. It needs no live-run data, so it
   was buildable immediately; it found and fixed five bugs in itself during development.
14. **A seventeenth skill, built then validated (v1.6.0 → v1.6.1).** `data-tier` proves a
   data-access change's *cost class* from its execution plan before a budget or profiler exists —
   N+1 detection, index usage, sequential-scan rejection. It was added as a *candidate* on the
   strength of two external critiques, with the explicit rule "validate it on a real N+1, not a
   document's say-so." `LIVE_RUN_002` did exactly that: running the suite against an 18k-LOC agent
   memory system, `data-tier` found a **proven** N+1 in the hot retrieval path (one DB query per
   graph neighbour, 41 round trips collapsible to 1). Candidate promoted to confirmed-good.
15. **The discipline proved itself by refusing a finding (v1.6.1).** In `LIVE_RUN_002`, an unlocked
   shared index under concurrent daemon threads *looked* like a data race — it reads completely
   true. The two-way test ran (6 threads, 1,600 concurrent adds) and showed zero corruption: the
   GIL serializes it. Per the suite's own law, a hypothesis whose two-way test fails **does not
   become a finding** — it was downgraded to a watch, not shipped as a verdict. This is the
   cleanest demonstration across both runs of why `(suspected)` may never wear a proof's costume.

16. **The suite audited itself (v1.6.2).** `LIVE_RUN_003` ran the full lifecycle with the suite as
   its own subject: ten skills bound to a real subject, seven correctly returned not-applicable
   (a doctrine repo has no slices, queries, trust boundaries, or releases — and forcing a verdict
   there would break Law 3). The same root cause — *the laws bind only a cooperative model* —
   surfaced from five independent lenses, stronger evidence than one reviewer asserting it once.
   Four findings were fixed: a degradation floor so an extracted skill keeps its constitution
   (PROTOCOL §6); a falsifiable acceptance criterion for Law 6, the suite's previously-untestable
   central invariant; the model-agnostic thesis honestly downgraded to `(suspected)` with a
   two-tier experiment written to settle it; and a both-sides boundary watch on the suite's
   thinnest mandate split. What it pointedly did **not** fix — the absence of a mechanical
   enforcement floor — is named as the real ceiling and the driver of the next run, not papered
   over.

## The one-line summary

**Frame falsifiably, decide reversibly, build provably, verify connectedly, gate adversarially,
debug causally, audit symptomatically, optimize measurably, scale sub-linearly, defend
adversarially, ship reversibly, migrate losslessly, maintain memorably — and at every step, know
exactly how much you know.**
