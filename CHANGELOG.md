# Changelog

Skill files are versioned artifacts (meta-skills Discipline 5). Changes are recorded here;
superseded behavior is described, never erased.

## 1.6.2 — 2026-06-22

**The suite audited itself, and fixed what that surfaced.** No new skill. This release is the
level-2 postmortem (Discipline 5) of running the full lifecycle against the suite as its own
subject — recorded in `LIVE_RUN_003.md`. Ten skills bound to a real subject, seven correctly
returned not-applicable (a doctrine repo has no slices, queries, trust boundaries, or releases —
forcing a verdict there would violate Law 3). Four findings, four fixes:

- **F1 — the extraction floor (PROTOCOL §6).** A skill copied out of the suite kept its evidence
  tags and silently lost every Law, the ledger registry, and the verdict grammar. §6 now states
  the **name-plus-clause rule** as the degradation floor: because every Law is cited by number
  *and* a ≤6-word naming clause, the citation is its own fallback — a skill conforms only if every
  Law it relies on appears name-and-clause in its own body, so a reader with no `PROTOCOL.md`
  recovers the rule's content, not just its number. Extraction now costs a skill its
  cross-references but never its constitution.
- **F2 — Law 6 made falsifiable (PROTOCOL §2).** "Constrain process, never intelligence" was the
  one invariant in the suite with no acceptance criterion. It now carries the **substitution test**:
  strip every concrete instance from a skill; if what remains still fully specifies the work, the
  skill constrains process; if a hole opens, that instance was load-bearing knowledge and is a
  Law 6 violation. Checkable by reading, **(trace-only)**.
- **F3 — the central thesis, honestly tagged.** The five "improves as models improve" claims are
  **(suspected)** by the suite's own vocabulary — nothing measured them. Law 6 now says so
  explicitly and points to the **two-tier experiment** specified in `LIVE_RUN_003.md` (fixed
  contract, two model tiers, pre-registered metrics, a stated falsifier) that would move the thesis
  to **(proven)**. The claim is no longer asserted as settled; it is now a falsifiable bet with a
  written test.
- **F4 — the thinnest mandate boundary, watched from both sides.** `scrutinize` and `senior-review`
  share ~60% of their method; the split (delta vs codebase) currently pays rent, so both wiring
  blocks now carry a boundary watch-item naming the merge signal (the two converging on one
  artifact) per mandate-boundary discipline. Kept, not merged — but no longer undocumented.

**Residual risk, unchanged and stated plainly:** the enforcement floor is still prose, not
mechanism. The four fixes above are **(trace-only)** — better words, exercised by no run. The
suite's one mechanical check (`verdict-lint.py`) still validates verdict-line grammar, not the
truth of claims. The next edit should be driven by the two-tier experiment or a CI hook that makes
one law mechanical — not by further design. (senior-review's `no enforcement floor` finding from
LIVE_RUN_003 is deliberately **not** closed here; it is the real ceiling and the honest next run.)

## 1.6.1 — 2026-06-22

**LIVE_RUN_002 — second live run, on an 18k-LOC system.** Ran the suite against `Tier-Memory`, a
real self-improving agent-memory system ~10× the size of LIVE_RUN_001's target and developed *with*
the suite (its `REVIEW_LEDGER.md` is written in the suite's own vocabulary). Hardest possible test:
disciplined author, cheap findings already swept. Results, all honestly tagged:

- **One proven finding (F1):** the hybrid-retrieval graph signal issues one DB query per graph
  neighbour — an N+1 whose round-trips grow with the knowledge graph. Proven by execution (40
  neighbours → 41 round trips, collapsible to 1). Fix shipped in `patches_tiermemory/`, with an
  honest non-mechanical caveat (graph-signal rank order) handed to the project's eval.
- **One disproved hypothesis (F2):** an unlocked `VectorIndex` under concurrent daemon threads
  *looked* like a data race. The two-way test ran (6 concurrent threads, 1600 adds) and showed zero
  corruption — the GIL serializes it at this granularity. Per the suite's own law, a failed two-way
  test does **not** become a finding; downgraded to a `(trace-only)` watch (free-threaded CPython /
  GIL-releasing C-ext would change this). This is the cleanest demonstration across both runs of why
  `(suspected)` may never wear a verdict's costume.
- **Two clean (F3 resolved ledger item `Score.__format__`; F4 loopback-bound daemon, one latent
  `--host 0.0.0.0` caveat).**

**What it taught the suite:**
- **`data-tier` is validated `(proven)` on first live use.** It was added in v1.6.0 as a *candidate*
  with the explicit caveat "build it from a real N+1, not a critique's say-so." This run is that
  N+1; the skill found a usage-scaling defect a line-by-line read would likely pass over. Promoted
  from candidate to confirmed-good.
- **No new mandate gap surfaced** (unlike LIVE_RUN_001, which spawned four skills). For an 18k-LOC
  single-process system the current seventeen were sufficient — itself signal that the suite may be
  near mandate-completeness for application-tier systems; the next gap, if any, is likeliest at the
  multi-process/distributed boundary.

Report: `LIVE_RUN_002.md`. Patch: `patches_tiermemory/01_graph_signal_batch.md`.

## 1.6.0 — 2026-06-22

**Seventeenth skill: `data-tier`** — proves a data-access change's *cost class* from its execution
plan, before a budget or profiler exists. Owns the previously-scattered question "does this query
scale worse than the data grows?" — N+1 detection, index usage, sequential-scan rejection,
cost-class-not-millisecond reasoning. Justified by the recurring data-tier gap two external
critiques raised AND by LIVE_RUN_001's own OR-filter/query findings; built as a *candidate* whose
first real edit should be driven by a live N+1 finding, not by the critiques' say-so. Conformed to
suite law on entry:
- Boundaries cut four ways, declared on both sides: perf-optimize (measures wall-clock against a
  budget; data-tier proves growth class before one exists — its findings become perf's Phase-4
  hypotheses), symptom-audit (felt complaint, trace-only cap; data-tier targets access cost and may
  reach proven via a plan), data-evolution (data-tier says *which* index and why; data-evolution
  ships it safely onto populated data), arch-design (data-model flaws).
- Evidence discipline is a PROTOCOL §1 pointer: reading SQL is (trace-only); an executed plan over
  a *representative distribution* is (proven), and the report states the distribution.
- Cost model is derived per-database, never a recited tuning manual (Discipline 6) — works on
  engines that don't exist yet.
- Registry: ledger `DATA_TIER.md` (§3), handoff row (§4), verdict noun `DATATIER:` + grep pattern
  (§5), chief-engineer routing row, validator registry; MAP/README/manifests → seventeen.

**`debug-protocol` enrichment** — Phase 3 (Localize) now escalates to **runtime inspection** (pause
at the suspect frame, read live variable/stack/heap state rather than infer it from source) as a
higher rung of the existing reproduce ladder. Tool-agnostic by design: the runtime's inspection
facility is *derived* like wire-check derives a framework's wiring; naming dlv/gdb/lldb would be a
ceiling (Discipline 6). Closes the "static-only debugging" concern from the external critique
without importing its tool-specific framing. Observed runtime state is (proven); inferred state is
(trace-only).

**On the two external critiques (assessed, not adopted wholesale):** most of their proposals were
already present and stronger (Socratic framing → problem-framing; TDD → build-discipline +
correctness-gate's mutation spot-check; Chesterton's Fence → Law 3; threat modeling → threat-model,
shipped v1.5.0). Two real points survived a scrutinize step-1 pass and became the above. Rejected
with reasons: `telemetry-sentinel` (a persistent monitoring daemon is a different product with
different failure modes, not a skill; the suite is invoked-per-request by design), and
`architectural-slicing`/AST context-pruning (a harness/runtime concern — a markdown contract cannot
purge its own context window; the legibility half is already meta-skills Discipline 6). Progressive
disclosure (split dense SKILL.md into references/) is noted as a future refactor, deferred until
density is observed to hurt rather than fixed preemptively.

## 1.5.0 — 2026-06-22

**The first real run, and the three skills + one tool it justified.** v1.3.1 flagged the suite's
#1 residual risk: every claim that it *works* was (trace-only) until a real project ran the full
lifecycle, and "the next change should be driven by that run's level-2 postmortem, not by further
design." This release is that change.

**LIVE_RUN_001** — the suite was executed against a real ~1,700-LOC Flask/SQLite ticket-booking
app (a size- and domain-matched stand-in, after the intended private `tickit` target was
unreachable from the run environment). It routed correctly, derived the system's invariants with
no checklist, and produced **seven findings, all (proven) by executing the real code** — a
forgeable admin token (full authorization bypass, minted with the repo's own committed key),
reversibly-encrypted passwords, overbooking past venue capacity (both by ignoring requested seat
count and by a TOCTOU race), a `unique=True` on a quantity column, and OR-filter lookups that
return unrelated rows. Full report + shipped patches in `LIVE_RUN_001.md` and `patches/`. The
lifecycle is now (proven) on foreign code, not (trace-only) on its own design.

**Level-2 postmortem → three new skills** (each passed the "no existing owner with a *pipeline*"
bar; a dimension that *catches* a finding is not a skill that *owns* the method):
- `threat-model` — adversarial security pipeline (assets → trust boundaries → abuse cases →
  abuse-case tests handed to correctness-gate). Owns what senior-review's "Safety & trust"
  dimension only flagged. Boundaries declared both ways: senior-review and correctness-gate now
  point security/hostile-test ownership here; this skill points structural trust-placement fixes
  to arch-design and pre-deploy clearance to ship-gate. It never claims "secure", only that named
  attacks are defended — its proofs cap at (trace-only) until the gate executes the tests.
- `ship-gate` — the previously unowned **act of shipping**: reversibility (no release without a
  proven rollback), bounded blast radius (staged over big-bang), observability-before-release, and
  a director-readable go/no-go. The suite's one-line summary ended at "ship" with nothing owning
  it; now the last door has an owner.
- `data-evolution` — persistent-data-shape change, whose rollback semantics differ fundamentally
  from code's (`git revert` restores code, not dropped columns). Owns expand-contract, dual-write,
  verify-on-a-copy, and the named point-of-no-return. evolve-maintain's deprecation ladder retires
  *code* callers; this retires *data*. Invoked by evolve-maintain and ship-gate.

**First mechanical enforcement** — `tools/verdict-lint.py`. The suite's standing residual risk is
"exhortation without enforcement". This validator parses verdict lines from a transcript/PR/log and
checks PROTOCOL §5 *form*: unregistered nouns, illegal states, trace-only verdicts missing their
required bold limitation marker, and success/failure contradictions on one line. It needs no
live-run data — it validates form, not correctness — so it was buildable today. It found and fixed
five bugs in itself during development (proven against the live-run report and adversarial
fixtures), per the suite's own "prove the tool" discipline.

**Process fix from the run** — chief-engineer's fast path is now *forbidden*, regardless of size,
when a slice touches a trust boundary or persistent data shape. LIVE_RUN_001 showed a 40-line diff
can bypass authentication or corrupt stored data; such slices route through threat-model /
data-evolution even when they would otherwise qualify as fast-path.

**Registry conformance** — PROTOCOL §3 (three new ledgers), §4 (three handoff rows), §5 (three
verdict nouns `THREAT:`/`SHIP:`/`MIGRATE:`, grep pattern extended); MAP/README/manifests updated to
sixteen; boundary declarations added on both sides for every new mandate.

**Residual risk, still honest:** the run used a *stand-in* for the intended `tickit` target — the
lifecycle is proven on real foreign code, but not yet on the user's own project. The three new
skills are themselves (trace-only) until a run exercises a security finding, a real deploy, and a
real migration end-to-end; that run should drive the next edit. The validator enforces *form*, not
*correctness* — it cannot tell a deserved GATE:pass from an undeserved one.

## 1.4.0 — 2026-06-12

**Thirteenth skill: `symptom-audit`** — symptom-scoped audit of an existing codebase, distilled
from a real audit run and abstracted. Owns the previously unowned question "where does a felt
complaint live, and what's the cheapest ranked path to relief?" Pipeline: Symptom → Map → Trace →
Sweep → Diagnose → Prescribe → Pre-verify. Conformed to suite law on entry:
- Mandate boundaries cut four ways and are stated on both sides: perf-optimize (runnable +
  measurable → there; its wiring now names symptom-audit as diagnostic front-end, and it stays
  the only skill that may claim measured gains), debug-protocol (broken vs slow-but-working),
  senior-review (whole codebase vs pinned symptom), wire-check (nothing happens at all).
- Its evidence discipline is a pointer to PROTOCOL §1, with the honest cap stated: read-only
  audits produce (trace-only) findings, and clean checks are findings too.
- "Verify" became **Pre-verify**: the skill pre-writes each phase's before/after check for
  perf-optimize / correctness-gate to execute — prescription and proof stay separated.
- Rewrite-scale causes escalate via arch-design as a separate decision, never inside a spec phase.
- The sweep checklist (perceived/latency/volume/waste/locality + cohesion) is explicitly the
  swappable, audit-type-specific part; the skeleton is audit-agnostic.
- Registry: ledger `AUDIT_SPEC.md` (PROTOCOL §3), handoff row (§4), verdict noun `AUDIT:` in the
  grep pattern (§5), chief-engineer routing rows split against perf-optimize, MAP/README/manifest
  counts updated to thirteen.

## 1.3.1 — 2026-06-11

**Fresh-eyes rule (PROTOCOL §8)** — separation of duties for review-class skills. When the
session that built a change runs `senior-review` or `scrutinize` on it, and stakes warrant, the
review runs in a fresh context (subagent / new session) from artifacts alone — never the build
conversation. Below the stakes bar, same-context review is legal but explicitly marked. A fresh
reviewer who cannot operate from artifacts alone has found a Law 2 defect by that fact alone.
Pointer lines added to both review skills. Closes the self-review blindness gap; the remaining
known gaps (no live run yet; prose without mechanical enforcement; nothing past "ship") are
recorded as the suite's own residual-risk statement below.

**Residual risk, stated honestly:** every claim that this suite *works* is (trace-only) until a
real project runs the full lifecycle. The next change to these files should be driven by that
run's level-2 postmortem (Discipline 5), not by further design.

## 1.3.0 — 2026-06-11

**Twelfth skill: `scrutinize`** — change-scoped, outsider second opinion on any not-yet-landed
delta (plan, design doc, PR, diff). Owns the previously unowned question "should this change
exist, and does it do what it claims?" Adapted from an external skill and conformed to suite law:
- Wiring block (consumes/produces/handoffs) — it arrived as an orphan skill.
- Informal claim-vs-verification rule replaced by the evidence vocabulary; cheap-execution
  escalation made binding.
- Its simpler-alternative pass now operationalizes meta-skills Discipline 7 (pointer, not a
  second statement, per Law 1).
- Law 3 guard on the outsider stance + mandatory ledger check (explained surprises are
  archaeology, not signal).
- Registry verdict line `SCRUTINY:` with a new `blocked(underspecified)` state; PROTOCOL §4/§5
  rows added; chief-engineer review routing split cleanly between senior-review (codebase) and
  scrutinize (delta); senior-review's wiring block states the boundary from its side.

## 1.2.0 — 2026-06-11

**The taste layer** — rigor was covered; these encode the instincts of great engineers:
- `meta-skills` Discipline 7 — Simplicity: the subtraction pass; complexity must be purchased by
  an invariant or measurement; abstractions on second use; deletion is a recorded win.
- `arch-design` — the dependency bar: a library enters only with build-it-ourselves cost,
  surface-used fraction, maintenance pulse, and a pin plan; default to writing small things.
- `chief-engineer` — spike mode: declared, timeboxed, quarantined throwaway exploration whose only
  durable output is knowledge in a ledger; spike code never graduates by merge. New routing row.
- `build-discipline` — smallest diff that satisfies the proof line (Phase 2); the short leash:
  full diff self-review before every commit, mandatory for generated code (Phase 5).
- `correctness-gate` — "look at the real thing": read actual outputs for real inputs, paste one
  representative pair into the verdict.

## 1.1.0 — 2026-06-11

**Wiring of the suite itself**
- `PROTOCOL.md` §0: where the suite root is from inside any install, and what "invoking a skill"
  means (open its SKILL.md, execute the contract; fall back to the §4 registry if absent).
- `chief-engineer` Phase 0: locate-and-load mechanics, stated where the router actually runs.
- `README.md`: CLAUDE.md bootstrap block so governed projects auto-route fresh sessions.

**Scaling mechanism (replaces the unenforced "lightweight by default" promise)**
- `PROTOCOL.md` §7: the scale rule — ledgers become files only when memory must outlive the
  session; otherwise inline under the ledger's heading, promotable verbatim.
- `chief-engineer`: concrete fast-path definition; two new routing rows (pure questions →
  no lifecycle; no-owner requests → named, never silently absorbed).

**Law 1 conformance**
- Decay rule was stated three times (PROTOCOL §1, build-discipline, meta-skills); now stated once
  with pointer-with-fallback references.
- Dangling bare-number Law references in debug-protocol now carry names; PROTOCOL §6 forbids bare
  numbers going forward.
- Evidence-tag glosses had drifted (three skills omitted **(suspected)**); PROTOCOL §6 now defines
  one canonical gloss, copied verbatim.

**Greppability**
- PROTOCOL §5 now carries the full verdict-line registry (all ten nouns + states) so one grep
  recovers any run's trajectory from a transcript.

## 1.0.0

Initial wired suite: eleven skills, PROTOCOL, MAP, plugin manifest.
