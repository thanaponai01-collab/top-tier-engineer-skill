# Changelog

Skill files are versioned artifacts (meta-skills Discipline 5). Changes are recorded here;
superseded behavior is described, never erased.

Entries below 2.0.0 were compressed in 2.1.0 to what each release *changed*. The argument for each
change is not here and never was: design decisions live in `DECISION_LEDGER.md`, and the runs that
earned the rules live in `runs/`.

## 2.2.0 — 2026-09-06 — the files nobody ever wrote

2.1.0 added `check-references.sh` and called it "the one thing that cannot recur silently." It
exempted every ALL_CAPS `.md` name, because a subject project's artifact cannot be checked for
existence from here. Under that exemption the suite had accumulated mandates for **14 artifact
files, 11 of which appear in zero of the eight runs in `runs/`** — `TODO_LEDGER.md` was ordered by
name 11 times across the skills and has never once been created.

- **The 11 unwritten mandates are gone**, the discipline kept: `TODO_LEDGER.md` → "a deferral
  row", `PERF_BUDGET.md` → "the budget", `MAINT_LOG.md` → "the intervention, append-only, per
  §3". PROTOCOL §3 already said *default to writing nothing to disk*; 2.0.0 simplified §3 and left
  19 skills still naming filenames it no longer wanted. The skills now route to §3 instead.
  Survivors are the five with a reader: `DEBT_LEDGER.md` (a tool parses it), `ARCHITECTURE.md`,
  `DECISION_LEDGER.md`, `PROBLEM_BRIEF.md`, `REVIEW_LEDGER.md`.
- **`repay_at` is documented.** `structure-report.py` has fired machine-checked repayment triggers
  since v1.19.0 and no skill mentioned the mechanism, so no agent could use it. `structure-gate`
  rule 4 now names it, and `build-discipline`'s deferral rule states the principle that makes it
  matter: **prefer a trigger a machine checks over one a human must remember to re-read** — a
  prose trigger fires only if someone re-reads the row at the right moment, which is why the prose
  rows rotted and the one machine-checked row worked.
- **The residue outside `skills/`**: README's paste-into-`CLAUDE.md` block listed 13 artifact names
  as "project memory" — the first surface a fresh agent reads, contradicting §3 outright. MAP's
  lifecycle diagram hardcoded six more; `DEBT_LEDGER.md` cited `TODO_LEDGER.md`'s rule for a file
  that no longer existed.
- **The exemption is now counted, not just skipped.** `check-references.sh` accumulates the
  exempted names and caps them (`subject_max=9`, locked at the measured number, not an aspiration).
  A mandate for a tenth artifact fails CI and names the offender. Verified by reintroducing
  `PERF_BUDGET.md` and watching it go red — the existence of a subject's artifact cannot be checked
  from here, but the suite's appetite for inventing them can.

Mandated artifact filenames 14 → 9, all nine with a reader. Gates green: `test_tools.py` 21 pass,
`STRUCTURE: held(accepted: 3, repaid: 0)`, references clean at 9/9 subject artifacts.

## 2.1.0 — 2026-09-06 — a gate for the residue, and the residue removed

2.0.0 deleted the suite's self-policing tools and the CI that ran them. The documents describing
that machinery stayed, and nothing noticed for a release.

- **The docs that named deleted machinery are gone.** `IMPROVEMENT_PLAN.md` (a plan for
  v1.19.0/v1.20.0 whose "run the full floor" command named tools that no longer exist),
  `STRUCTURE_REPORT.md` (a checked-in copy of a v1.17.0 tool run), `DEBT_LEDGER` rows D-4/D-5/D-6,
  README's 108-line design history (CHANGELOG holds the same content, versioned), and MAP's skill
  table (the fourth copy of the twenty; PROTOCOL §4 owns it).
- **`run-trace.py` and `protocol_vintage.py` deleted, with the mandate that called them.**
  run-trace read a transcript file that `stop-gate.py` wrote, and stop-gate was deleted in 2.0.0 —
  so `chief-engineer` Rule 4's "do not self-report completeness without it" was an order with no
  input. Rule 4 now names the stages and their verdict lines directly. PROTOCOL §5 drops the
  `TRACE` noun; §9's rule-vintage clause goes with the module that was its one owner.
- **The five `agents/` wrappers stated the same isolation contract verbatim.** It lives once in
  PROTOCOL §6; each agent keeps only what makes it different. 159 → 117 lines.
- **Section drift fixed at 25 sites.** Tools cited "§10 rule 5" and "§11" of a PROTOCOL that ends
  at §9 — every cross-reference they printed to a director was wrong. `DECISION_LEDGER` D003 and
  D007 get a superseding line rather than an edit; the ledger is append-only history.
- **CI exists again** (`.github/workflows/gates.yml`), running three gates on push and PR: the tool
  tests, the debt ratchet, and a new `tools/check-references.sh` — every file the live surface names
  must exist. That last one is the defect class this release repaired, so it is the one thing that
  cannot recur silently. `CHANGELOG.md`, `DECISION_LEDGER.md` and `runs/` are exempt: naming a
  deleted file is what history is for.
- Also: `structure-report.py --thresholds` removed (no caller, no test, no doc);
  `structure_opacity.py` and `_encoding.py` lose the essays defending them.

Gates green: `test_tools.py` 21 pass, `STRUCTURE: held(accepted: 3, repaid: 0)`,
`LATENT: findings(dead: 0, unused: 0)`, references clean.

## 2.0.0 — 2026-09-06 — the subtraction release: half the doctrine, none of the self-policing

A director field report: "when using, it over explained, sometimes it gives me the structure 2
times in the chat... the doctrine I don't know if it's over-complicated words. This must be a skill
that helps me, not drag me." A ponytail-audit found two separate causes and one theme.

**The doubled output was an install problem, not a doctrine problem.** The suite was installed
three times at once — the plugin, twenty symlinks in `~/.claude/skills` pointing at a second
checkout, and two frozen May copies of `senior-review` and `wire-check` (13 KB each) that were not
symlinks and shadowed the current 4 KB versions. Every skill was registered twice, so its structure
could be emitted twice. Both loose installs and the second checkout are gone; the plugin is the
only registered copy.

**Seven of ten tools existed only to audit the auditor.** `verdict-lint`, `registry-check`,
`doctrine-budget`, `cadence-check`, `stop-gate`, `_registry_source`, their tests, the 250-line CI
workflow, and the Stop hook that could refuse to end a session over a malformed verdict line — all
deleted. Only three tools were ever invoked during real work (`graph-audit`, `structure-report`,
`run-trace`); those and their tests remain, 31 tests green. The enforcement floor was real
engineering, and it was engineering aimed at this repo rather than at the director's systems.

**The doctrine surface halved.** `PROTOCOL.md` 399 lines → 209, rewritten in plain words:
"don't let known problems grow" for the ratchet rule, "how sure are you?" for the evidence
vocabulary, "does it make sense?" for the sense floor. `PROTOCOL_RATIONALE.md` (314 lines) and
`GATE_DOCTRINE.md` (74) are deleted — a 209-line protocol needs no scoped subset, so the `agents/`
gates now load §1 and §5 of the real file. Sections renumbered: old §8 fresh-eyes → §6, §9 fix →
§7, §10 ratchet → §8, §11 sense floor → §9, §7 scale → §3. Old §6 (degradation) and §12 (run
cadence) are gone: the gloss was pasted into 19 skills for a scenario that never occurred, and §12's
only enforcement was `cadence-check.py`.

**Every skill lost its boilerplate.** The 20 KB of per-skill "Wiring" blockquotes restated
PROTOCOL §4's table, in violation of the suite's own first rule; each is now one line naming the
question that skill owns. The DELIVERY-block paragraph was copied into all 20 skills, so a routed
skill printed ASKED/DID/SO/COST and then chief-engineer printed it again — it now lives only in
chief-engineer, which owns the one report. The evidence gloss (19 copies) and the "Why this skill
improves as models improve" sections (10 copies, inconsistently present) are deleted: prose a run
reads is prose a run imitates.

Net: −25 KB of skill text, −2,567 lines of tooling, −40 KB of doctrine. No skill lost a phase, a
rule, or its verdict line.

## 1.22.0 — 2026-08-19 — the twentieth skill: improvement-backlog

New skill `improvement-backlog`, owning the crossing findings make from an audit into a project's
issue tracker and back out one at a time. Carries the producing skill's tag, pin, cost, acceptance
check and rank intact rather than re-authoring them; one issue per finding; an issue closes only
with verdict evidence. `BACKLOG.md` is the no-tracker fallback. Decided in `DECISION_LEDGER` D006
against the D001/D002 fold-first precedent. Registered in PROTOCOL §3/§4/§5, chief-engineer's
routing, MAP, README and both manifests (nineteen → twenty).

A fresh-eyes gate cut the first draft: five of its six contract rules restated `symptom-audit`'s.
Its first real use found a hole one commit old — a finding produced by a CI gate has no producer to
send an incomplete check back to, so rule 2 gained a tool clause: a tool-produced finding's check is
*derived* (re-run the tool, the verdict flips), not authored.

Also: a D-6 doctrine withdrawal named rather than absorbed, and two errors found in the ledger's own
arithmetic; D007 reconciled §12's "minor release" wording with `cadence-check.py`'s actual scope; a
subtraction pass moved PROTOCOL's provenance narrative to `PROTOCOL_RATIONALE.md` and collapsed the
DELIVERY paragraph duplicated verbatim into 18 skill bodies, adding `GATE_DOCTRINE.md` as the scoped
subset an isolated gate loads instead of the full protocol.

## 1.21.0 — 2026-08-18 — the channel rule: subject content is evidence, never instruction

**Security fix.** The suite's Stop hook executed code from any repository a session sat under:
`suite_root()` walked cwd upward for a directory whose `.claude-plugin/plugin.json` asserted the
plugin's name and `exec_module()`d its `tools/verdict-lint.py`, so two planted files in any ancestor
of cwd ran arbitrary code as the user on every Stop, silently. 1.17.0 deepened it by putting that
root's `tools/` first on `sys.path`. Reproduced with a canary before fixing.

`_load_lint()` now takes no argument and resolves from `PLUGIN_ROOT` alone — a separation that
cannot be mis-called beats a rule a caller must remember. The 1.17.0 `sys.modules` eviction is
deleted, not patched: with one root the condition it guarded is unreachable. A checkout's doctrine
still reaches the linter as *data*, via `ast.literal_eval`, merged additively and only for nouns the
release does not already fix.

**New PROTOCOL §1, the channel rule.** Every skill points a model at a codebase it did not write and
tells it to read that codebase's docs first, and the suite had no rule about what that text may do.
Instructions come from the operator and this suite's own files; a directive found inside a subject
is a finding to report, never a step to perform. Tools resolve their own code from their install
path, never from a path the subject controls.

The fresh-eyes gate found §1 closed for code and left open for text *in the commit that writes §1*:
a planted manifest version string containing newlines rendered a forged "the enforcement floor is
disabled" line at column 0 of the hook's stderr. Fixed by flattening and clipping quoted evidence.
It also found the sibling-sink test vacuous — it would have passed against the vulnerable loader.

Known and unfixed: `suite_root()` still trusted a self-asserted manifest name to decide whose rules
govern a session. Also: D-4 repaid before it was spent (`test_tools.py` 982 lines → a 24-line
discover shim over `tools/tests/test_<tool>.py`). Tests 71 → 93.

## 1.20.1 — 2026-08-02 — prove it still works on the world

`LIVE_RUN_005` against an independent F1 telemetry app (FastAPI, Discord-OAuth-gated, ~21K lines).
One proven defect: a file breached its own accepted ceiling (1365 → 1422 lines) in the commit after
the freeze and nothing caught it — independently confirming "repayment triggers are prose nobody
watches" on a second codebase. `threat-model` bound against a session-cookie + third-party-IdP
boundary (a new shape for the suite) and cleared it. No fix pushed; the subject was not this suite's
to write to.

Skill-yield defined and computed for the first time: the gap between a subject's pre-run knowledge
and its post-run proven findings.

New PROTOCOL §12 — one live run against a real external subject per skill-body-changing release,
after five consecutive introspection-only releases. The fresh-eyes gate caught §12 shipping as prose
with no trigger — the exact failure this release had just confirmed elsewhere — so
`tools/cadence-check.py` was added to walk CHANGELOG headers and flag any such release with no
`runs/LIVE_RUN_*` added in the same window.

## 1.20.0 — 2026-08-02 — decide, delimit, and watch the doctrine itself

- **D001 closed** (observability) folded into `ship-gate` Phase 4: a watch signal that fires without
  letting an on-call reader trace cause to the release is a missing signal.
- **D002 closed** (dependency intake) into `arch-design`'s dependency bar, which gains license and
  license-compatibility.
- **D005 opened and closed**: any behavior touching a resource reachable by more than one caller
  gets its check-and-claim sequence written as its own oracle row in `correctness-gate` Phase 2.
  Earned by a landed race-condition fix with no owning mandate.
- **The knowledge tier named** (PROTOCOL §2): Law 6 bans a load-bearing particular from a skill
  *body* and never said anything about `tools/` or reference files, where a sanctioned exception
  already lived unnamed. Legal there, provided every entry is data a tool consumes and is labelled
  illustrative-and-overridable.
- **Repayment gets an owner**: `evolve-maintain` gains intervention class **Repay**, auto-routed on
  `STRUCTURE: repayment-due(...)`.
- **The doctrine budget measured for the first time** (`tools/doctrine-budget.py`), frozen as D-6.

A fresh-eyes gate caught the first draft closing D001/D002/D005 with `status: decided` and no
traceable ruling event, contradicting the ledger's own schema — each now carries explicit ruling
provenance.

## 1.19.0 — 2026-08-02 — rewire, then repay

Nine of nineteen skills surfaced with no trigger description in a real session — proactive
triggering is the whole premise, and half the suite was soft-unwired.

- Every skill's frontmatter description compressed to pure trigger text (≤250 chars; chief-engineer
  ≤400), with boundary prose moved to the body. A bulk edit flattening descriptions to plain YAML
  scalars broke one file (an unquoted colon-space is a mapping separator); all descriptions moved to
  block-scalar form, which is immune to the hazard class.
- The Stop hook stopped hardcoding `python`, which does not exist on stock Debian/Ubuntu/macOS — the
  hook had been failing silently on every non-Windows install. Interpreter now selected by
  `command -v`, after a first fix (`python3 ... || python ...`) was caught re-running the gate with
  drained stdin and turning a block into a fail-open pass.
- D-5 repaid: six tools carried an inline UTF-8 guard in two drifted variants, four guarding stdout
  only and leaving stderr crashable under cp1252 — the exact bug the row existed to describe.
  Extracted to `tools/_encoding.py`.
- Repayment triggers became machine-checked: baseline entries may carry `"repay_at": N`, and
  `structure-report.py` emits `STRUCTURE: repayment-due(...)` when a debt crosses its own expiry.

## 1.18.0 — 2026-08-02 — the registry that was declared twice

§5's noun→state mapping lived in the doctrine table and in `verdict-lint.py`'s `REGISTRY`, with
nothing checking they agreed — and a reconciler was impossible because §5 was not machine-readable
as one structure: `FIX` and `TRACE` declared their states in prose beneath the table. Both gained
rows, and `tools/registry-check.py` now reconciles table against linter on every CI run.

## 1.17.0 — 2026-07-29 — the gates that could not fail

A design audit of the suite's own folder; eleven findings, all proven. The theme: several rules were
declared shared and implemented local, or pointed at a path that could not contain anything.

- **`runs/` was in `.gitignore`, so two of four CI gates were structurally vacuous.** They globbed a
  directory this repo has never had, printed "gate passes vacuously" on every run, and could not
  fail — while `PROTOCOL.md` cited those transcripts by name six times as the provenance of its own
  rules. Every citation was a dead link for anyone who installed the plugin. `runs/` now ships,
  redacted (`DECISION_LEDGER` D004).
- **§11's rule vintage was declared general and implemented in one tool** — `verdict-lint`
  privately, `run-trace` not at all, so run-trace enforced a 1.13.0 rule against transcripts
  declaring `PROTOCOL: 1.12.0`. Extracted to `tools/protocol_vintage.py`.
- `graph-audit.py` said "this is a gap, not a clean result" in the paragraph and `LATENT: clean` in
  the machine-readable half every grep reads. Now reports `layer-breaches: UNMEASURED`.
- `LATENT` and `FIX` were not in run-trace's known nouns, so no `latent-audit` run had ever been
  checkable for completeness.
- The evidence-tag gloss had drifted in ten of nineteen skills; `scrutinize` had no isolation agent,
  despite §9 making it mandatory on every delivered fix.

The scrutinize gate, added by this release, was run against this release and found a blocker in it:
GitHub Actions runs `run:` under `bash -e`, so a new "exit 2 = skip" branch was unreachable and the
gate would have hard-failed on the exact commit that un-vacuumed it. The ratchet also caught its own
author — a fix landed inside a function already on the debt ledger and pushed it 88 → 101 lines.

## 1.16.1 — 2026-07-29 — consistency sweep: the seams between artifacts

Every mechanical floor was green and four real defects sat in the seams between artifacts.

- The release-drift gate compared `plugin.json` against `CHANGELOG.md` and didn't know about
  `marketplace.json`, which carries its own version — so the gate written because "this drift
  shipped twice" was green while a third surface disagreed. All three must now agree.
- A self-test asserted a fact about the *checkout directory* rather than the code, passing in CI only
  because GitHub names the repo differently from the plugin. It failed in a clone named after the
  plugin: green in CI, red on the author's machine.
- §11 was enforced across nineteen skills and stated in two, so a conformant standalone run was
  blocked by the Stop hook for a rule its own contract never stated.
- `STRUCTURE_REPORT.md` was in the §4 handoff chain with no row in the §3 registry.

## 1.16.0 — 2026-07-29 — the sense floor: does the delivered thing answer what was asked?

Earned by a director's use report: *"it missed some thing that i always find when using it — like
the make sense thing."* Three failures confirmed as the ones actually felt: it's not what I meant,
way too much for the job, and I can't tell what it did.

The mechanism: a director's words are read once, by `problem-framing`; every stage after consumes a
*derived* artifact. Grepped across the suite — no skill anywhere re-read the original request, so
drift from intent was structurally invisible. `GATE: pass` is fully compatible with having built the
wrong thing at the wrong size.

New PROTOCOL §11 (the sense floor) and meta-skills Discipline 8. Every director-facing report opens
with four lines before any verdict: ASKED (quoted, never paraphrased — the paraphrase *is* the
drift), DID, SO (no engineering vocabulary), COST (files, concepts, steps, things that can break —
never lines written or tests added). No threshold for "too much" is defined and none may be; the
floor is that the price is visible next to the job.

Enforcing it condemned four historical transcripts, which forced the general fix: **rule vintage**.
A transcript declares `PROTOCOL: <version>`; checks younger than that declaration are skipped for
it; an undeclared transcript is judged by current rules, so the mechanism can never be used to opt
out. The four legacy transcripts were annotated, never retouched.

## 1.15.0 — 2026-07-27 — the debt ratchet: stopping accumulation by defensible increments

Earned by a real miss: a dashboard reached **4,180 lines in one file** — ~3,000 of them an
HTML/CSS/JS front end inside a single Python string — while every slice along the way was proven,
wired and committed. No gate ever saw a violation because no increment ever was one.

- **Code inside string literals was invisible.** To `ast` that front end is one `Constant` node: the
  report counted 61 functions and 0 of the 40 embedded ones, and emitted zero complexity, nesting
  and length findings over the most dangerous mass in the file. Every zero was correct. New signal
  `opaque_code` in `tools/structure_opacity.py`, naming no language: ask the file's own lexer which
  tokens are string or comment, then judge what is inside by content-free shape statistics (indent
  levels, line-length variance). A first cut matching markers, and a second cut scoring bracket
  depth and `;`/`}` terminators, both encoded the C family rather than code — the second scored Lua
  as prose. Guarded by a test using Lua and an invented syntax.
- **Coverage is now reported on every run**, and promoted to a general rule: a measurement's
  denominator is part of the measurement. A region the analyzer never entered is *unmeasured*, and
  in a report that omits coverage, unmeasured is indistinguishable from clean.
- **The god-file check never ran on non-Python files** — `file_lines` lived inside
  `analyze_python()`, so the same 3,000 lines extracted to a real `.js` file scored zero.
- **The ratchet** (PROTOCOL §10): a point-in-time gate re-asks "is this file too long?" and keeps
  earning the same correct answer while the file triples. Accepted breaches freeze in
  `.structure-baseline.json`; the gate then fails only on a breach that is new or worse. New
  `DEBT_LEDGER.md`, every row carrying what it costs per future change and a repayment trigger. The
  one forbidden move: re-baselining to turn a red gate green.
- **`build-discipline` was pointing at the debt**: "smallest diff" is measured against the slice,
  not the file it lands in, so on an overloaded host it points at appending to the god-file.
- **The Stop hook could not survive its own suite growing** — found by the hook blocking the session
  that wrote this release. A session adding a verdict state could never stop: the transcript emits
  the new state, the installed release's registry doesn't know it, the gate blocks. The release
  check had also been inert in the hook path since the day it shipped.

## 1.14.1 — 2026-07-04 — self-audit follow-ups

`PROTOCOL.md` said "the eighteen skills share" while the suite had been nineteen since 1.5.0 — drift
in the file that arbitrates drift. A new `SuiteConsistency` guard derives the count from `skills/*/`
on disk and asserts every count surface matches. `verdict-lint --help` stopped crashing with a raw
traceback. New `DECISION_LEDGER.md` recording D001 (observability) and D002 (dependency intake) as
open mandate questions rather than silently improvised.

The first cut of the count guard covered 2 of 5 surfaces; the §9 FIX gate forced a `scrutinize` pass
that caught the gap before the fix could be called coherent — the delivered-fix discipline working
on its own author.

## 1.14.0 — 2026-07-03 — latent-audit: the no-symptom sweep

No skill owned "audit this codebase — find dead code, check layer correctness, find real bugs" when
nothing *felt* wrong: `symptom-audit` refuses entry without a complaint, `senior-review` answers
wisdom not evidence, and no tool measured layer direction or reachability.

New skill `latent-audit` and new tool `tools/graph-audit.py` (one import/reference graph, three
checks: layer-direction breaches against a declared order, dead-module candidates, unused top-level
defs). Core law: statically unreferenced is **(suspected)** dead, never proven — no path from
suspected to deleted without a three-step disconnection proof, each deletion its own revertable
commit. Self-applying it to the suite exposed a real false-positive class (unittest classes
discovered by reflection).

Authored in parallel with 1.13.0 against the same base; lands as 1.14.0 to keep the version line
monotonic.

## 1.13.0 — 2026-07-03 — the first external audit becomes rules with teeth

An outside engineer audited `LIVE_RUN_004` and found three failure classes. The run stands
unretouched; the checks exist so its failures cannot recur silently.

- **Pin rule (§1).** The run quoted a function signature that does not exist at the subject's pushed
  revision, and nothing recorded which revision it was read from. Every report now carries
  `SUBJECT: <name> @ <revision>`; file:line quotes are evidence at that revision only.
- **Baseline rule (§1).** The run ranked severity against an *imported* invariant that the subject's
  own quoted evidence contradicted — the data was open to insiders by design, so the true asset was
  leaked-token blast radius, a tier lower and differently named. Consequence is now measured as the
  delta over the subject's evidenced intent; invariants carry provenance (inherited / evidenced /
  imported).
- **Delivered-fix discipline (§9).** The run delivered a fix while recording "scrutinize (no delta)";
  the unadjudicated fix gated on a decorative predicate and left a surface-parity incoherence. A
  delivered fix is now a delta, closing with a `FIX` line.

## 1.12.0 — 2026-07-02 — the tools stop being trusted on their own word

~1,000 lines of tooling shipped with zero tests and had already regressed twice. New
`tools/test_tools.py` exercises each tool through its real CLI, and found two live bugs on first
run: `verdict-lint` printed `§` without reconfiguring stdout to UTF-8, and `structure-report`
crashed on `os.path.relpath` when the scanned path and cwd sit on different Windows drives.

The §8.2 parallel gates ship as isolated subagents in `agents/`, so fresh-eyes review is reproducible
instead of re-improvised per release. Run provenance moved under `runs/`.

## 1.11.0 — 2026-07-02 — the enforcement floor becomes mechanical

Every rule had depended on the model choosing to comply. The plugin ships a Stop hook that runs
`verdict-lint` over the session transcript: a malformed verdict, an illegal state, or a trace-only
close without its limitation marker blocks the stop. Fails open on internal errors and respects
`stop_hook_active`, so it can never wedge a session. `verdict-lint --release` checks `plugin.json`
against the top CHANGELOG heading — that drift had shipped twice.

## 1.10.0 — 2026-07-02 — the model-aware layer

The contracts constrained process but were silent about the *executor* — a model with a training
cutoff, an environment it may not be able to execute in, and a documented tendency to patch-thrash.

- **The cutoff rule (§1):** recollection of any external interface — library API, CLI flags, wire
  format, version — is **(assumed)**, never (trace-only), until verified against this environment's
  ground truth. The highest-frequency real-world model failure mode, and no rule covered it.
- **Executability census** in chief-engineer Phase 1: whether the environment can run the code sets
  the evidence ceiling of the whole run, so it is established while reading ground rather than
  discovered at the point of failure.
- **The thrash rule** (Discipline 5): a second failed fix on the same symptom is proven evidence the
  fixes did not hold — reroute to `debug-protocol`, no third attempt without a proven cause.
- **§8.2, the independence corollary:** artifacts-only gates share no conversational state and may
  run concurrently. Fresh eyes stop costing wall-clock time.

## 1.9.2 — 2026-07-02

`run-trace.py` gained a security-audit profile. A pure `threat-model` run could not be
completeness-checked: `THREAT` was absent from the tool's profiles, so a security audit was either
declared complete with zero checking or misclassified as a review and falsely flagged — both
reproduced by executing the tool.

## 1.9.1 — 2026-06-26

`run-trace.py` crashed on Windows consoles on its `✅/❌/⛔` glyphs (same failure mode as
`structure-report.py` in 1.8.0), and its own `human_report()` tripped the length threshold on first
self-scan — extracted at authoring, no Chesterton's Fence on brand-new code.

## 1.9.0 — 2026-06-26 — run-completeness made visible

The skills are contracts the agent reads, not code that runs, so a director who can't read code
couldn't tell whether a run executed the stages it should have. New `tools/run-trace.py` infers the
request type from verdict presence and reports whether every verdict that kind of work requires is
present. Honest by construction: a missing required verdict is proven evidence a stage was skipped;
a present one is only trace-only evidence it ran.

Self-applied to the live runs: `LIVE_RUN_001` and `002` come back incomplete (they predate the
discipline — cause was in prose, not a verdict). Recorded honestly, not retrofitted.

## 1.8.0 — 2026-06-26 — mechanical enforcement floor

Enforcement was entirely prose-based: `verdict-lint.py` existed but nothing invoked it, no CI
existed, and nothing measured structural quality.

New `tools/structure-report.py` (complexity, nesting, function/file length, import cycles,
duplication; stdlib-only) and new skill `structure-gate`, which measures shape and routes every flag
to `senior-review`/`scrutinize` for the wisdom call, never deciding wisdom itself. New CI workflow
blocking merge on breach — the first mechanical "no" in the suite. Self-applied on first use: the
only open finding was routed rather than auto-refactored to silence the gate.

PROTOCOL §8.1: the fresh-eyes rule is satisfied by a context-isolated invocation or by the CI gate;
`(same-context review)` is no longer legal when the CI gate could have served as reviewer.

Also: `structure-report.py` crashed on Windows consoles on its glyphs before printing its verdict
line — failing its own acceptance criterion on the director's OS; and `verdict-lint` read transcripts
without `utf-8-sig`, so a BOM-saved file hid its first verdict line and the gate passed vacuously.

## 1.7.1 — 2026-06-25 — self-audit fixes

`chief-engineer`'s frontmatter described it as routing *"twelve specialist skills"* while the suite
had been seventeen since 1.6.0. PROTOCOL §5's recovery grep could not match `SLICE <name>:` or
`MAINT <ID>:` — the only two nouns carrying an identifier before the colon — so trajectory recovery
silently dropped every build and maintenance verdict. `verdict-lint`'s own regex was already correct;
the grammar doc now agrees with the tool.

## 1.7.0 — 2026-06-25 — audit-report findings addressed

Six targeted fixes from an external audit. `verdict-lint` stopped exempting SLICE and MAINT from
state validation, narrowed the trace-only bold-marker check from "any `**` within 16 lines" to a
paragraph-level bold line within 8, and gained sequence validation for the three §4 chain invariants
most likely to be violated by a skipped skill.

The scrutinize/senior-review merge signal became falsifiable: >70% overlap of file:symptom pairs in
one engagement, rather than "if the two converge". Two handoff orderings pinned: `data-tier` closes
before `perf-optimize`; `evolve-maintain` closes before `data-evolution` runs as a peer. Discipline 5
now requires independent validation — the session proposing a skill edit cannot approve it.

## 1.6.2 — 2026-06-22 — the suite audited itself

The full lifecycle run against the suite as its own subject (`LIVE_RUN_003`). Ten skills bound;
seven correctly returned not-applicable — a doctrine repo has no slices, queries, trust boundaries
or releases, and forcing a verdict there would violate Law 3.

- **The extraction floor (§6).** A skill copied out of the suite kept its evidence tags and silently
  lost every Law. Every Law is now cited by number *and* a ≤6-word naming clause, so the citation is
  its own fallback: extraction costs a skill its cross-references, never its constitution.
- **Law 6 made falsifiable (§2)**, via the substitution test: strip every concrete instance from a
  skill; if what remains still specifies the work, it constrains process; if a hole opens, that
  instance was load-bearing knowledge.
- **The central thesis honestly tagged.** The five "improves as models improve" claims are
  **(suspected)** by the suite's own vocabulary — nothing measured them.

Residual risk stated plainly: the enforcement floor is still prose, not mechanism.

## 1.6.1 — 2026-06-22 — second live run, ~18k-LOC external codebase

Against a system ~10× the first run's target, authored by a disciplined developer with the cheap
findings already swept.

- **One proven finding:** a hot read path issuing one query per collection element — dozens of round
  trips collapsible to 1. Fix shipped.
- **One disproved hypothesis:** an unlocked shared index under concurrent threads *looked* like a
  data race. The two-way test ran (6 threads, 1600 adds) and showed zero corruption — the GIL
  serializes it at this granularity. Per the suite's own law a failed two-way test does not become a
  finding; downgraded to a trace-only watch. The cleanest demonstration across both runs of why
  (suspected) may never wear a verdict's costume.

`data-tier` was validated on first live use, having shipped in 1.6.0 as a candidate. No new mandate
gap surfaced, unlike the first run, which spawned four skills.

## 1.6.0 — 2026-06-22 — seventeenth skill: data-tier

Proves a data-access change's *cost class* from its execution plan, before a budget or profiler
exists — N+1 detection, index usage, sequential-scan rejection. Boundaries cut four ways against
`perf-optimize`, `symptom-audit`, `data-evolution` and `arch-design`. The cost model is derived
per-database rather than recited, so it works on engines that don't exist yet. Built as a candidate
whose first real edit must be driven by a live N+1, not by the critiques that suggested it.

`debug-protocol` Phase 3 escalates to runtime inspection — pause at the suspect frame and read live
state rather than infer it from source — tool-agnostically, since naming dlv/gdb/lldb would be a
ceiling.

Two external critiques assessed rather than adopted: most proposals were already present and
stronger. `telemetry-sentinel` rejected (a monitoring daemon is a different product, not a skill)
and AST context-pruning rejected (a harness concern — a markdown contract cannot purge its own
context window).

## 1.5.0 — 2026-06-22 — the first real run, and the three skills it justified

`LIVE_RUN_001` executed the suite against a real ~1,700-LOC Flask/SQLite booking app. It routed
correctly, derived the system's invariants with no checklist, and produced **seven findings, all
proven by executing the real code**: a forgeable admin token minted with the repo's own committed
key, reversibly-encrypted passwords, overbooking past venue capacity (both by ignoring requested seat
count and by a TOCTOU race), a `unique=True` on a quantity column, and OR-filter lookups returning
unrelated rows. The lifecycle became proven on foreign code rather than trace-only on its own design.

Three new skills, each passing the "no existing owner with a *pipeline*" bar — a dimension that
*catches* a finding is not a skill that *owns* the method:

- `threat-model` — the adversarial pipeline (assets → trust boundaries → abuse cases → abuse-case
  tests handed to correctness-gate). It never claims "secure", only that named attacks are defended.
- `ship-gate` — the previously unowned act of shipping: reversibility, bounded blast radius,
  observability-before-release. The suite's one-line summary ended at "ship" with nothing owning it.
- `data-evolution` — data-shape change, whose rollback semantics differ from code's: `git revert`
  restores code, not dropped columns.

Also: first mechanical enforcement (`tools/verdict-lint.py`, checking §5 form), and chief-engineer's
fast path forbidden regardless of size when a slice touches a trust boundary or persistent data
shape — the run showed a 40-line diff can bypass authentication.

## 1.4.0 — 2026-06-12 — thirteenth skill: symptom-audit

Owns "where does a felt complaint live, and what's the cheapest ranked path to relief?" Pipeline:
Symptom → Map → Trace → Sweep → Diagnose → Prescribe → Pre-verify. Boundaries stated on both sides
against `perf-optimize` (runnable and measurable goes there, and it stays the only skill that may
claim measured gains), `debug-protocol` (broken vs. slow-but-working), `senior-review` (whole
codebase vs. pinned symptom) and `wire-check` (nothing happens at all).

"Verify" became **Pre-verify**: the skill pre-writes each phase's before/after check for another
skill to execute, so prescription and proof stay separated.

## 1.3.1 — 2026-06-11 — the fresh-eyes rule (PROTOCOL §8)

When the session that built a change reviews it and stakes warrant, the review runs in a fresh
context from artifacts alone. Below the stakes bar, same-context review is legal but explicitly
marked. A fresh reviewer who cannot operate from artifacts alone has found a Law 2 defect by that
fact alone.

Residual risk stated: every claim that this suite works is trace-only until a real project runs the
full lifecycle, and the next change should be driven by that run rather than by further design.

## 1.3.0 — 2026-06-11 — twelfth skill: scrutinize

Outsider second opinion on any not-yet-landed delta. Owns "should this change exist, and does it do
what it claims?" Adapted from an external skill and conformed to suite law: it arrived as an orphan
with no wiring block, and its informal claim-vs-verification rule was replaced by the evidence
vocabulary. Review routing split cleanly — `senior-review` owns the codebase, `scrutinize` the delta.

## 1.2.0 — 2026-06-11 — the taste layer

Rigor was covered; these encode the instincts of great engineers.

- `meta-skills` Discipline 7, Simplicity: the subtraction pass; complexity must be purchased by an
  invariant or a measurement; abstractions on second use; deletion is a recorded win.
- `arch-design`: the dependency bar — a library enters only with build-it-ourselves cost,
  surface-used fraction, maintenance pulse and a pin plan.
- `chief-engineer`: spike mode — declared, timeboxed, quarantined; spike code never graduates by
  merge.
- `build-discipline`: smallest diff that satisfies the proof line; full diff self-review before every
  commit, mandatory for generated code.
- `correctness-gate`: look at the real thing — read actual outputs for real inputs.

## 1.1.0 — 2026-06-11 — wiring of the suite itself

PROTOCOL §0 (where the suite root is from inside any install, and what "invoking a skill" means) and
chief-engineer Phase 0. New §7 scale rule: ledgers become files only when memory must outlive the
session.

Law 1 conformance: the decay rule had been stated three times and is now stated once; evidence-tag
glosses had drifted, with three skills omitting **(suspected)**. §5 gained the full verdict registry
so one grep recovers any run's trajectory.

## 1.0.0

Initial wired suite: eleven skills, PROTOCOL, MAP, plugin manifest.
