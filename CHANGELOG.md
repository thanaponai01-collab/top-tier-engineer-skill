# Changelog

Skill files are versioned artifacts (meta-skills Discipline 5). Changes are recorded here;
superseded behavior is described, never erased.

## 1.11.0 — 2026-07-02

**The enforcement floor becomes mechanical.** Until now every rule depended on the model
choosing to comply — the exact residual risk verdict-lint's own docstring names. This release
wires the harness in: the plugin now ships a `Stop` hook (`hooks/hooks.json` →
`tools/stop-gate.py`) that extracts assistant text from the session transcript and runs
`verdict-lint` over it at every session stop. A malformed verdict, an illegal state, or a
trace-only close without its bold limitation marker now *blocks the stop* (exit 2) until fixed;
sessions with no verdict lines pass silently, so the gate costs nothing outside suite runs.
The gate fails open on its own internal errors and respects `stop_hook_active`, so it can
never wedge or loop a session.

- **verdict-lint `--release <root>`** — plugin.json version must equal the top CHANGELOG
  heading. This drift shipped twice (v1.7.1 router, v1.9.2→1.10.0 manifest); it is now a
  mechanical check, run automatically by stop-gate when the session cwd is the plugin repo
  itself, and runnable standalone in CI.
- **`tools/stop-gate.py --selftest`** — the tools directory gets its first executable check:
  asserts a malformed verdict blocks, a clean transcript passes, the loop guard holds, and
  the plugin's own manifest/CHANGELOG agree. (proven — selftest executed green at release.)

## 1.10.0 — 2026-07-02

**The model-aware layer: the suite now names its executor's own failure modes.** Until this
release the contracts constrained *process* but were silent about the *executor* — a model with a
training cutoff, an environment it may not be able to execute in, and a documented tendency to
patch-thrash. Four additions, each a process constraint (Law 6, constrain process never
intelligence — no solutions hard-coded), each stated once (Law 1, every rule lives in exactly one
place) with pointers elsewhere. No new skill; count stays eighteen. Fresh-context review performed
per Discipline 5 (isolated context, artifacts + diff only): **CONFIRM-WITH-FIXES** — both required
wording fixes applied in the follow-up commit (build-discipline pointer trimmed to Law 1 pointer
form; thrash rule reconciled with debug-protocol's trigger and its (proven) claim tightened to
what execution actually showed).

- **PROTOCOL §1 — the cutoff rule** (sibling of the decay rule). Model recollection of any
  external interface — library API, CLI flags, wire format, service behavior, version — is
  **(assumed)**, never (trace-only), until verified against this environment's ground truth
  (installed source/types, `--help`, lockfile pin, live docs). Reading promotes to (trace-only);
  executing promotes to (proven). This is the highest-frequency real-world model failure mode
  (interface drift past the training cutoff) and no rule covered it. Pointer added in
  build-discipline Phase 2: interfaces from ground truth, not memory.
- **chief-engineer Phase 1 — executability census.** Whether the environment can run the code and
  tests sets the evidence ceiling of the entire run; it is now established during ground-reading
  and stated in the report's first lines, instead of being discovered at the point of failure.
- **meta-skills Discipline 5 — the thrash rule.** A second failed fix on the same symptom is
  (proven) evidence the fixes did not hold; treat the cause as not-found and reroute to
  `debug-protocol` — no third attempt without a proven cause. debug-protocol's trigger already
  fires at the first fix that didn't hold; this count is the hard floor a session may never
  cross, stated where the always-on disciplines bind, never permission for a second blind attempt.
- **PROTOCOL §8.2 — independence corollary (parallel gates).** Gates that consume only artifacts
  (correctness-gate, structure-gate, threat-model, senior-review on the same change) share no
  conversational state by §8's own isolation requirement, so they may run concurrently as
  isolated contexts where the harness supports it. §4 sequencing rules still bind; verdicts merge
  into chief-engineer's one report. Fresh eyes stop costing wall-clock time.
- **Manifest version drift fixed (proven, trivially).** `plugin.json` still said `1.9.0` while
  this changelog was at `1.9.2` — the same class of self-description defect as v1.7.1's router
  scope mis-statement. Bumped to `1.10.0`.

## 1.9.2 — 2026-07-02

**`run-trace.py` gained a security-audit completeness profile (proven gap from LIVE_RUN_004).**
Running the suite against TickIt (a real Next.js app with a Supabase/RLS trust boundary) surfaced a
proven blind spot: a pure `threat-model` run could not be completeness-checked. `THREAT` was absent
from the tool's `PROFILES`, `NOUN_TO_TYPE`, `TYPE_PRIORITY`, and `PHRASE_HINTS`, so a security audit
was either declared "complete" with zero checking (false green — `TRACE: complete(unclassified…)`)
or misclassified as a `review` run and falsely flagged as missing REVIEW (false red) — both
reproduced by executing the tool. Added a `threat` profile (required: THREAT) and registered the
noun. Placed below `review` in `TYPE_PRIORITY` so combined review+threat runs are unchanged;
LIVE_RUN_001/002/003/004 all trace identically after the change. No new skill; count stays eighteen.
`verdict-lint.py` already knew `THREAT` (tools/verdict-lint.py:38), so the gap was isolated to
`run-trace.py`. Invoker unchanged: chief-engineer Phase 4 Rule 4 and CI gate 3 already call the tool.

## 1.9.1 — 2026-06-26

**Two authoring-hygiene fixes to `tools/run-trace.py` found by the enforcement-floor self-check.**

- **`run-trace.py` UTF-8 portability (proven bug).** The tool crashed on Windows consoles (cp1252) on its `✅/❌/⛔` glyphs — same failure mode as `structure-report.py` in v1.8.0. Fixed with the same one-line guarded `sys.stdout.reconfigure(encoding="utf-8")` in `main()`.
- **`run-trace.py` `human_report()` cleaned at authoring.** On first self-scan the tool flagged its own `human_report()` (67 lines > 60 threshold). As brand-new code in this commit (no Chesterton's Fence), the stage-rendering section was extracted into `_format_stage_result()` — `human_report()` now dispatches and `_format_stage_result()` renders. Re-scan: clean (1 open flag, the pre-existing `_check_sequence()` item). Consistent with v1.8.0's treatment of `structure-report.py`'s own `main()`.

## 1.9.0 — 2026-06-26

**Run-completeness made visible (second self-discovered blind spot closed).** The skills are
contracts the agent reads, not code that runs, so a director who can't read code couldn't tell
whether a run executed the stages it should have. The verdict lines were the trace, but nothing
checked them for completeness-by-request-type. Added the checker; no new skill, count stays
eighteen.

- **New tool `tools/run-trace.py` — "did it actually build?"** Reads a run transcript, infers
  the request type (build / fix / review / scrutinize / ship / perf / audit / structure) from
  verdict presence (falling back to phrase hints), and reports whether every verdict that kind of
  work REQUIRES is present — in plain language a non-coder acts on. Complete / incomplete /
  no-trace, with a `TRACE:` verdict line and matching exit code. Honest by construction: a missing
  required verdict is (proven) evidence a stage was skipped; a present one is only (trace-only)
  evidence it ran — stated in the tool's own output, never upgraded to a correctness claim.
- **CI gains a third gate.** `enforcement-floor.yml` now runs run-trace on committed transcripts
  and blocks on incompleteness, with a non-coder-readable summary line.
- **Law-1 boundary held.** verdict-lint owns form+ordering; run-trace owns
  completeness-for-request-type; the tools don't call each other and don't duplicate rules.
  `TRACE` registered in verdict-lint REGISTRY as a tool-output noun (no skill owner), documented
  in PROTOCOL §5.
- **Self-applied to the live runs.** `RUN_TRACE_REPORT.md` records each LIVE_RUN's completeness.
  LIVE_RUN_001 and LIVE_RUN_002 come back incomplete (missing CAUSE — they predate the discipline;
  cause was in prose, not a verdict). LIVE_RUN_003 complete. Recorded honestly; not retrofitted.
- **chief-engineer Rule 4 updated.** The one-report contract now requires citing the run-trace
  result — completeness is surfaced in the report, not left for the director to wonder about.

## 1.8.0 — 2026-06-26

**Mechanical enforcement floor closed (the highest-severity open finding since v1.6.2).**
Enforcement was entirely prose-based: `verdict-lint.py` existed but nothing invoked it, no CI
existed, and nothing measured structural quality. This release adds the floor and gives the suite
an owner for measured structure. New skill → **eighteen** total (17 specialists + dispatcher).

- **New tool `tools/structure-report.py` — the structural-quality instrument.** Measures
  cyclomatic complexity, nesting depth, function/file length, import cycles, and duplication;
  emits a plain-language "is this spaghetti?" verdict a non-coder can act on, plus a machine
  `STRUCTURE:` line. stdlib-only (Python-deep; language-agnostic line+duplication for other
  languages, honestly scoped). Self-applied on first use against the suite's own source: the only
  open finding is `verdict-lint._check_sequence()` at cyclomatic 17 — **recorded and routed to
  `senior-review`** in `STRUCTURE_REPORT.md` per the measure-never-judge contract, **not**
  auto-refactored to silence the gate.
- **New CI workflow `.github/workflows/enforcement-floor.yml`.** Runs `structure-report` and
  `verdict-lint` on every push/PR and **blocks the merge on breach** — the first mechanical "no"
  in the suite, independent of any agent's self-report. Writes a non-coder-readable pass/fail
  summary to the GitHub step summary. By design it reports **red** on the open routed
  `_check_sequence` finding until `senior-review` rules — the red badge *is* the routing signal,
  not a defect.
- **New skill `structure-gate`.** Owns measured structural quality (passed the no-existing-owner
  test); measures shape and routes every flag to `senior-review`/`scrutinize` for the wisdom call,
  never deciding wisdom itself. Wired into PROTOCOL §4/§5 (new verdict noun `STRUCTURE`), MAP,
  README, chief-engineer routing, and both manifests.
- **PROTOCOL §8 strengthened — author≠reviewer is now a harness obligation (§8.1).** The
  fresh-eyes rule is satisfied by a context-isolated invocation or by the CI gate (context-free by
  construction); the `(same-context review)` marker is no longer legal when the CI gate could have
  served as the independent reviewer.
- **Two install-time fixes (this run), both proven on the director's own machine.**
  - *`structure-report.py` UTF-8 portability.* The reporter crashed on Windows consoles (cp1252)
    on its `✅/⚠️` glyphs *before* printing the verdict line — failing its own acceptance criterion
    on the director's OS. Fixed with a one-line guarded `sys.stdout.reconfigure(encoding="utf-8")`;
    no-op where stdout is already UTF-8 (CI).
  - *`structure-report.py` `main()` cleaned at authoring.* On first self-scan the tool flagged its
    own `main()` (complexity 19, 108 lines). As brand-new code in this commit (no Chesterton's
    Fence), it was split into `analyze()` (measurement) and `print_human_report()` (rendering) —
    the tool's own source now scans clean. Distinct from the `verdict-lint` finding, which is
    pre-existing and left for `senior-review`; the difference is provenance, not double standard.
  - *`verdict-lint.py` BOM tolerance.* The CI gate lints `*_RUN_*.md` transcripts; one saved with
    a UTF-8 BOM (common on Windows editors) would hide its first verdict line behind a leading
    byte-order mark, so the gate passed vacuously. Switched the transcript read to `utf-8-sig`,
    which strips a BOM if present and is identical otherwise — the floor no longer has a silent
    bypass.

## 1.7.1 — 2026-06-25

**Self-audit fixes (chief-engineer lifecycle run on the suite itself).** No new skill; three
consistency/recovery defects closed at lowest viable scope.

- **Router mis-stated its own scope.** `chief-engineer`'s frontmatter described it as turning
  *"twelve specialist engineering skills into one"* while the suite has been seventeen since v1.6.0.
  Corrected to *"sixteen specialist engineering skills"* (16 specialists + the dispatcher = 17),
  matching the count in PROTOCOL.md, README.md, MAP.md, and both manifests.
- **PROTOCOL §5 recovery grep was wrong for two nouns.** The documented one-grep
  `^(LIFECYCLE|…|MAINT):` could not match the real verdict forms `SLICE <name>:` and
  `MAINT <ID>:` — the only two nouns carrying an identifier before the colon — so trajectory
  recovery silently dropped every build and maintenance verdict. Added the optional name segment
  `( [^:]+)?` before the colon. `verdict-lint.py`'s `NOUN_RE` already handled this correctly; the
  grammar doc now agrees with the tool.
- **`verdict-lint.py` dead code removed.** The unused `GREP_PATTERN` constant carried the same
  name-segment bug as the §5 grep while its comment claimed it was "extended" — a misleading
  artifact. Deleted; the name-segment allowance is now documented on the live `NOUN_RE`.

## 1.7.0 — 2026-06-25

**Audit-report findings addressed.** No new skill. Six targeted fixes from the external audit
report (`top-tier-engineer-audit-report.md`), each closing a named gap at the lowest viable scope.

- **P2 — `verdict-lint.py`: three gaps closed.**
  - *Gap 2a*: SLICE and MAINT were exempt from state validation ("free-form"). Both have defined
    legal states; only LIFECYCLE (genuinely free-form stage labels) is now exempt.
  - *Gap 2b*: the trace-only bold-marker check matched any `**` within 16 lines — too wide and
    semantically blind. Now requires a line *beginning* with `**` (paragraph-level bold statement)
    within 8 lines, distinguishing a purposeful limitation declaration from incidental inline bold.
  - *Gap 2c*: no sequence validation existed. Added `_check_sequence()`: flags `GATE: pass` with
    no preceding `SLICE: proven`, `SHIP: go/stage` with no preceding `GATE: pass`, and `MIGRATE`
    with no preceding `SHIP` or `MAINT` — the three §4 chain invariants most likely to be violated
    by a skipped skill or out-of-order transcript.
- **P4 — scrutinize / senior-review merge signal made falsifiable.** The boundary watch-item in
  both skills previously said "if the two converge on one artifact, collapse them" — undetectable
  without human judgment. Now stated as a measurable threshold: if >70% of file:symptom pairs
  overlap in the same engagement, the boundary has collapsed. Qualitative convergence is not the
  signal; quantitative overlap at threshold is.
- **P5 — handoff sequencing gaps closed in PROTOCOL §4.** Two boundary pairs had no ordering rule
  when both fired on the same artifact: (a) data-tier + perf-optimize: DATATIER closes first,
  findings arrive as Phase-4 hypotheses afterward; (b) evolve-maintain → data-evolution:
  evolve-maintain closes its MAINT verdict immediately, then data-evolution runs as a peer.
  verdict-lint.py's sequence check enforces (b) mechanically.
- **P7 — Discipline 5 loop now requires independent validation.** The postmortem session that
  proposes a skill edit cannot also approve it (fresh-eyes rule, Law 4, PROTOCOL §8, applied to
  the suite itself). Fresh-context review is now required; same-context edits accepted only
  provisionally, marked `(same-context review)` in the changelog. All fixes in this release are
  `(same-context review)` — the rule was not in force when they were written.
- **P8 — patches corpus linked to evidentiary record in MAP.md.** The `patches/` and
  `patches_tiermemory/` directories are now referenced in `MAP.md` with an explicit description of
  what each proves and why the finding delta is the closest thing to a measurable skill yield.

**Not addressed (deferred by design or requiring live runs):**
- P1 (CI enforcement), P3 (two-tier experiment), P6 (right-side pipeline), P9 (CI category gap) —
  unchanged and stated plainly in the audit report.

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
