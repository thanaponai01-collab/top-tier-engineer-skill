# DECISION_LEDGER.md — the suite's own consequential decisions

Owner: `arch-design`. Append-only. Schema (PROTOCOL §3, arch-design §Record):
`ID | date | decision | options | forces | reversibility class | evidence tag | status`.
Superseding never deletes — future models need the archaeology. Every entry carries ≥2 options
and a reversibility class. Open questions live here as `status: open` until the director rules.

---

## D001 — Should observability be its own mandate, or stay folded into ship-gate + evolve-maintain?

- **date:** 2026-07-04
- **decision:** **Option 1 — fold, as today.** `ship-gate` Phase 4 (Observability) gains an explicit
  diagnosability check: a watch signal that fires without letting an on-call reader trace cause is
  treated as a missing signal and routed to `evolve-maintain` before go/no-go. No new skill.
- **forces:** Raised by the v1.14.0 self-audit. No skill owns "is this observable in prod — are
  the right signals emitted, can an incident be diagnosed from what we log?" Today it is split:
  `ship-gate` owns "watch signals" for a release, `evolve-maintain` owns learning from incidents
  after they land. Neither owns *designing* observability into a change before it ships. The
  counter-force is Law 3 (Chesterton's Fence): the split may be deliberate, and a nineteenth-plus
  skill for a dimension two skills already touch risks bureaucracy the suite exists to kill.
- **options:**
  1. *Fold, as today* — extend `ship-gate`'s watch-signals phase with an explicit "diagnosability"
     check (can the named rollback trigger actually be observed?). No new skill. **(recommended
     pending evidence)** — cheapest, and no live run has yet produced a finding that had no owner.
  2. *New `observability` gate* — a dedicated skill owning signal design, run parallel to
     `threat-model`. Justified only if a real run surfaces an observability finding that neither
     `ship-gate` nor `evolve-maintain` could own — the same evidence bar that justified
     `threat-model`/`ship-gate`/`data-evolution` in v1.5.0 (`LIVE_RUN_001`).
- **reversibility class:** two-way. Folding first and splitting later costs one skill add; the
  reverse (deleting a skill) is the expensive direction, so start folded.
- **evidence tag:** (suspected) — no live run has surfaced an unowned observability finding yet;
  closed on the precedent that a two-way-door decision may be settled by a director-directed
  session rather than waiting indefinitely for a live run (D003 was a director-reported gap
  resolved this way), per IMPROVEMENT_PLAN.md F5.
- **ruling provenance:** this entry's own schema (line 6 of this file) requires `status: open`
  "until the director rules." The ruling here is the director's explicit instruction to continue
  `IMPROVEMENT_PLAN.md` Phase 2, which names "F5 ledger decisions (D001/D002/D005)" as directed
  work in its execution-order table — not this session inventing the ruling unprompted. A
  fresh-eyes `scrutinize` gate flagged the absence of an explicit attribution line here before
  this note was added; this is that correction.
- **status:** decided — closed as option 1, shipped in 1.20.0 (`ship-gate` Phase 4 diagnosability
  check). Promotable to option 2 if a live run later surfaces a finding the check can't own.

## D002 — Should "taking a new dependency" be an owned decision, or stay in ponytail prose?

- **date:** 2026-07-04
- **decision:** **Option 1 — arch-design checklist.** `arch-design` Phase 3 point 4 (the dependency
  bar) now requires license and license-compatibility alongside the cost/surface/maintenance-pulse
  checks it already carried, and is explicitly named as this decision's home.
- **forces:** The cutoff rule (PROTOCOL §1) verifies an external interface's *behavior*;
  `evolve-maintain` owns dependency *updates*. Nothing owns the gate *before* a dependency enters:
  its CVE surface, license, maintenance health, and whether a few lines of stdlib would do
  (ponytail ladder rung 5). That judgment currently lives only in ponytail prose, which is
  guidance, not a gate with a verdict line — so a dependency can be added with no recorded
  adjudication. Counter-force: dependency choice is an architecture decision, and `arch-design`
  already owns "which technology, recorded reversibly" — this may need a *checklist in arch-design*,
  not a new mandate.
- **options:**
  1. *Add a dependency-intake checklist to `arch-design`* — a new-dependency decision must record
     the stdlib/native alternative considered, license, and CVE/maintenance check as a
     `DECISION_LEDGER` entry. No new skill; reuses the existing "technology names live in
     decisions" rule. **(recommended)** — closes the gap where it already half-lives.
  2. *New `dependency-gate` skill* — a dedicated supply-chain gate. Heavier; justified only if
     arch-design's ledger proves too coarse in a real run.
- **reversibility class:** two-way. A checklist in arch-design can be promoted to a skill later if
  evidence demands; the reverse is costly.
- **evidence tag:** (suspected) — pattern-level concern, no live run has shipped a bad dependency
  through the suite yet; closed on the same director-directed-session precedent as D001, per
  IMPROVEMENT_PLAN.md F5.
- **ruling provenance:** same as D001 — the director's explicit instruction to continue
  `IMPROVEMENT_PLAN.md` Phase 2 is the ruling this entry's schema requires, not a self-graded
  closure; added after a fresh-eyes `scrutinize` gate flagged its absence.
- **status:** decided — closed as option 1, shipped in 1.20.0. Promotable to option 2 if arch-design's
  ledger proves too coarse in a real run.

---

*Provenance: D001/D002 opened by the v1.14.0 chief-engineer self-audit ("check the system, find the
gaps"). They record gaps the suite does not yet own, per PROTOCOL §4's rule that a missing mandate
is logged, not silently improvised. Both closed in 1.20.0 (IMPROVEMENT_PLAN.md F5) under the
director's explicit instruction to execute that plan's Phase 2 — see each entry's ruling-provenance
line, added after a fresh-eyes `scrutinize` gate found the original closures undertraceable.*

---

## D003 — Where does the "sense floor" live: a new gate skill, or the always-on layer?

- **date:** 2026-07-29
- **decision:** **Always-on layer** — `meta-skills` Discipline 8 (the discipline) + `PROTOCOL.md`
  §11 (the definition, the DELIVERY block, and the enforcement scope), with `chief-engineer`
  Phase 4 as the single place the whole run is checked against the request.
- **forces:** The director reported the gap as present in *"every tools and skills"*, not at one
  stage — and the mechanism confirms it: the miss is that no stage downstream of `problem-framing`
  ever re-reads the original request, so a gate placed at the end would inherit the same blindness
  it is meant to cure (it too would consume derived artifacts). A twentieth skill would also have
  to be *routed to*, and the failure is precisely that nobody notices there is anything to route.
  Counter-force: the always-on layer is the most expensive place to add a rule, since it binds
  inside every phase of every skill — and Discipline 7, simplicity, applies to this suite too.
- **options:**
  1. *Discipline 8 + §11 + `chief-engineer` Phase 4* **(chosen)** — binds everywhere the gap was
     reported, adds no stage to route to, and reuses `verdict-lint` for teeth. Cost: the always-on
     layer grows a seventh… eighth discipline, and every report pays four lines.
  2. *A `sense-gate` skill (twentieth mandate)* — a parallel §8.2 gate answering "does this answer
     the ask?". Rejected: it must be routed to by the same run that cannot see the problem, and it
     would consume artifacts rather than the request — reproducing the defect inside the fix.
  3. *Strengthen `problem-framing` only* — re-check the brief against the request at the end.
     Rejected as too narrow: it addresses fit, and leaves proportion and legibility ungated. It
     also fires at the wrong end, since `problem-framing` does not run in most sessions.
- **reversibility class:** two-way for the *placement* (a discipline can be promoted to a skill if
  a live run proves prose insufficient); one-way-ish for the *DELIVERY block shape*, since once
  reports carry `ASKED/DID/SO/COST` and `verdict-lint` enforces it, changing the field names
  invalidates every transcript's vintage baseline. Field names were therefore chosen for a
  non-coder reader, not for symmetry with the verdict grammar.
- **evidence tag:** **(proven)** for the mechanism (grepped: no skill re-reads the original
  request) and for the enforcement (8 tests, exit codes verified). **(suspected)** for the claim
  that the DELIVERY block actually changes what a director feels — that needs a live run under
  1.16.0 to settle, and the experiment is: does a report whose `COST` line is honest change any
  director decision that a 1.15.0-style report did not?
- **status:** decided — shipped in 1.16.0.

## D004 — Does the run ledger (`runs/`) ship in the public repo?

- **date:** 2026-07-29
- **decision:** **Ship it, redacted.** `runs/` is tracked from v1.17.0; subject identities are
  replaced by stable pseudonyms (`SUBJECT_A/B/C`), local paths removed, and one copy-paste
  invocation against a live subject with an open finding was reduced to a stated check. Every
  finding, evidence tag, verdict line and `file:line` reference is the original.
- **forces:** The v1.17.0 design audit found `runs/` in `.gitignore`, which produced two
  independent defects. (1) `PROTOCOL.md` cites `AUDIT_001` and `LIVE_RUN_00x` by name six times
  as the *provenance* of its rules — the pin rule (§1), the baseline rule (§1), all of §9 — and
  four more times across MAP and the skills; every one was a dead link for any reader who
  installed the plugin, which is Law 2, artifacts outlive conversations, failing at exactly the
  point it matters most. (2) The two CI gates that lint transcripts globbed `**/*_RUN_*.md` and
  `run-logs/`, so with the evidence untracked they printed "passes vacuously" on every run and
  *could not fail* — while four transcripts failed `run-trace` locally. Counter-force, and it is
  a real one: the repo is public and the ledger documents security findings in systems the
  director owns, one of them open at the time of writing. Publishing evidence and protecting a
  subject pull in opposite directions, and no gate in the suite arbitrates that — it is a
  director call, and was taken as one.
- **options:**
  1. *Ship redacted* **(chosen)** — keeps every citation resolvable and makes both CI gates real,
     at the cost of one redaction pass and a permanent obligation: every future run added to
     `runs/` must be redacted before it is committed.
  2. *Ship as-is* — maximum evidentiary value, strongest reading of Law 2. Rejected: it publishes
     an actionable description of an unfixed authorization gap in a live system, and git history
     makes that irreversible.
  3. *Keep private, delete the citations* — rewrite each rule to justify itself inline. Rejected:
     it closes the dead-link problem by deleting the evidence rather than by shipping it, and
     leaves the two transcript gates permanently vacuous, which is the larger defect.
  4. *Private sibling repo, cite by ID* — evidence intact, but a public reader still cannot follow
     the citation and the gates here stay vacuous. Rejected as the cost of (3) plus the cost of a
     second repo.
- **reversibility class:** **one-way.** Publication cannot be undone — git history and indexing
  outlive a later deletion. This is why it was escalated rather than decided by the run.
- **evidence tag:** **(proven)** for the mechanism (`git ls-files runs/` returned 0 of 42 tracked
  files; the CI globs match nothing in a checkout; `run-trace` exited 1 on four transcripts) and
  for the redaction (re-scanned: zero remaining subject identifiers or local paths). **(assumed)**
  that pseudonymisation is sufficient — it defeats identification from the text, not correlation
  by a reader who already knows the director's projects.
- **status:** decided — shipped in 1.17.0. The standing obligation it creates (redact before
  committing a run) belongs with whoever adds the next transcript.

## D005 — Does concurrency/atomicity get an owning skill, or a checklist row in correctness-gate?

- **date:** 2026-08-02
- **decision:** **Option 1 — checklist row in `correctness-gate`.** Phase 2 (Oracle) now requires
  that any surfaced behavior touching a resource reachable by more than one caller gets its
  check-and-claim sequence written down as its own property-oracle row, rather than left implicit
  inside Phase 3's generic "concurrent" boundary case.
- **forces:** `runs/patches/03_capacity_and_race.md` is a real race-condition fix the suite shipped
  against an external subject — a shared-resource check-and-capacity guard that read occupancy
  unlocked before writing, overbooking under concurrent requests. No skill's mandate names
  concurrency/atomicity by name: `correctness-gate` proves a change against *stated* criteria, and
  a race is exactly the defect class nobody states as a criterion until it fires. This is the
  run-earned evidence D001/D002 never had — a live finding with no clean owner, which is precisely
  the evidence bar those two decisions were waiting on. Counter-force: a full `concurrency-gate`
  mandate would be the twentieth skill for one defect class that already has a home (Phase 3
  already lists "concurrent" among the hostile-input cases) — the gap is that it's implicit, not
  that it's unowned.
- **options:**
  1. *Checklist row in `correctness-gate`* — the atomicity property is named explicitly in Phase 2
     so it must be enumerated per-behavior, not left to Phase 3's generic case to catch by luck.
     No new skill; reuses the existing oracle-enumeration machinery. **(recommended, chosen)** —
     the run-earned defect was a *missing oracle*, not a missing skill; `correctness-gate` already
     owns "no oracle → untestable-as-specified," this just stops concurrency from hiding inside a
     catch-all.
  2. *New `concurrency-gate` mandate* — a dedicated skill for shared-resource safety, parallel to
     `threat-model`. Rejected for now: one run-earned finding is enough to name the gap, not enough
     to justify a twentieth mandate when the existing oracle mechanism can enumerate it directly.
     Revisit if a future live run shows the checklist row insufficient (e.g., a distributed-systems
     subject where atomicity spans processes, not just one datastore's transaction).
- **ruling provenance:** opened and closed in the same session under the director's explicit
  instruction to continue `IMPROVEMENT_PLAN.md` Phase 2, which names opening-and-deciding D005 as
  directed work — the ruling this entry's schema requires, not a self-graded closure. Added after
  a fresh-eyes `scrutinize` gate flagged its absence in the original entry.
- **reversibility class:** two-way. A checklist row can be promoted to a skill later if evidence
  demands; the reverse (deleting a skill) is the expensive direction, so start with the row.
- **evidence tag:** **(proven)** for the mechanism — `runs/patches/03_capacity_and_race.md` is a
  landed fix, not a hypothetical — and **(trace-only)** for the claim that naming the oracle row
  would have caught it pre-ship (the fix predates this decision; no gate ran against the named row
  yet).
- **status:** decided — shipped in 1.20.0. Promotable to option 2 if a future run shows the row
  insufficient for a harder concurrency shape.

## D006 — Findings → issue tracker → implement-one-by-one: an owning skill, or a fold?

- **date:** 2026-08-19
- **decision:** **Option 1 — new skill `improvement-backlog`**, owning the previously unowned
  question *"did a finding survive the crossing into a tracker intact, and did the close carry
  evidence?"* — **resized mid-decision by the fresh-eyes gate**, see the rescope note below.
- **forces:** A director field report (§12 field-report admissibility — the same door §10 and §11
  entered through) describes a recurring real workflow: *"ive been trying to find improvement in
  any area codebase. architechtual codebase. ui and ux. try to make things work. and all those
  will be output to issue on repo where i can start implement one by one from there GitHub
  issue."* The suite's audit skills produce findings into ledger files; **(proven)** — grep of
  `skills/`, `PROTOCOL.md`, `MAP.md` for `issue tracker|github issue|backlog|gh issue` returns
  zero hits — nothing owns externalizing findings to a tracker, and nothing owns the pickup/close
  loop (an issue closed with no verdict evidence is invisible to every gate). Counter-force, the
  D001/D002 precedent: fold first, split later. But those folds worked because the gap was a
  *checklist row inside an existing mandate*; here the gap is an artifact schema + a loop, and
  §3's own pattern requires every ledger one owner skill — the tracker used as a ledger is a
  ledger.
- **options:**
  1. *New skill `improvement-backlog`* **(chosen)** — owns the finding→issue schema (evidence tag,
     pin, pre-written acceptance check carried into every issue), the impact-per-effort ranking,
     and the close-with-evidence discipline. Distinct trigger vocabulary the director actually
     uses ("output to issues", "implement one by one"). Generation of findings stays with the
     audit skills; routing stays with chief-engineer.
  2. *Fold: chief-engineer routing rows + a PROTOCOL externalization paragraph* — rejected:
     chief-engineer's mandate is routing, not artifact schemas; a schema stated in PROTOCOL with
     no owner skill breaks the §3 one-owner pattern, and PROTOCOL bytes are the D-6 budget's
     scarcest resource.
  3. *Fold into `evolve-maintain`* — rejected on mandate: its subject is interventions on a live
     system and `MAINT_LOG.md` is append-only history, while audits also run pre-maintenance.
     But the *shape* it demonstrates was the strongest counter-argument here and the first draft
     never engaged it: `IMPROVEMENT_PLAN.md` B3 closed a comparable gap with "one new class in an
     existing skill; no new mandate" (the `Repay` class), against the director's own complaint
     that the suite adds gates rather than improving what it has. What defeats it for this gap is
     that the residue is not an intervention class at all — it is an artifact leaving the suite's
     custody for a tracker, and returning later with no session attached.
  4. *Fold into `symptom-audit`* (Phase 6/7 gain a delivery target: emit the prescription as
     issues) — **the nearest neighbour, and the option the first draft of this entry omitted.**
     Rejected only after the skill was resized: a producing skill can emit its own findings, but
     the close-with-evidence loop runs *after every producer has closed*, and findings from two
     different producers naming one cause can only be merged by something downstream of both.
     Had the skill kept its first draft's scope — where it restated collapse, ranking, and
     pre-written checks — this option would have been correct and the skill wrong.
  5. *Fold into `TODO_LEDGER.md`* (owned by `build-discipline`) — rejected: that ledger holds work
     deferred *inside* a build, each row carrying a trigger that makes it due, and it is
     in-repo memory for the same team's next slice. An externalized backlog is the opposite
     direction — findings leaving the artifacts for a tracker a human drains. The two are linked
     from each other, never merged; the new skill names duplicating those rows as an anti-pattern.
- **ruling provenance:** the director's own request in this session — "can we make them a skill
  to improve this skill?" — is the ruling, per the D001 precedent that a director-directed
  session may settle a two-way-door decision.
- **rescope (§8.1(a) fresh-eyes gate, same session, no build context):** the gate returned
  `SCRUTINY: rework` against the first draft and was right on the load-bearing count — five of six
  contract rules restated `symptom-audit`'s (collapse, impact-per-effort ranking, pre-written
  checks, the Law-3 question, the evidence-tag row), which is Law 1, every rule lives in exactly
  one place, violated inside a skill written to serve Law 2. The skill was cut to the residue no
  upstream skill owns — the crossing into a tracker, and the close after every producer has
  closed — with the upstream rules now carried by reference rather than restated (its contract
  rule 1, *carry, never re-author*). It also ships the falsifiable merge signal the gate asked
  for: a boundary watch naming `symptom-audit` and the observation that would settle it. Recorded
  because a decision that changed shape under review is archaeology a future model needs; the
  first draft's scope is described here, not erased.
- **reversibility class:** two-way for the contract (a skill can be demoted to prose; the
  `BACKLOG` noun stays registered either way, and an unused noun costs one registry row).
  Deleting the skill outright is the expensive direction, but the mandate is field-evidenced,
  not speculative.
- **evidence tag:** **(proven)** for the ownership gap (the grep above); **(trace-only)** for the
  workflow description (the director's report, taken at its word per §12); **(suspected)** for
  the claim the skill will change outcomes — the next real backlog run settles it.
- **status:** decided — shipped in 1.22.0 with `runs/LIVE_RUN_006.md` as the §12 evidence.

## D007 — §12 says "minor release"; `cadence-check.py` enforces it on every release — which is right?

- **date:** 2026-08-19
- **decision:** **Option 3 — a skill-body change is semantically minor and must never ship as a
  patch.** `cadence-check.py`'s `evaluate()` was already correct: it applies the run-cadence check
  to any release ≥ `CADENCE_INTRODUCED_AT` that changed a skill body, with no minor/patch split,
  because a body change is a behavior change and is therefore never patch-level in its own right —
  the defect was that §12 never said so. No change to the tool's logic; §12's prose and the tool's
  docstring both gain the explicit statement (this commit).
- **forces:** Issue #4 — §12's text scopes the obligation to "minor release[s]"; the code compares
  the whole version tuple with no such split. **(proven)** — executed against the pure
  `evaluate()` (no git/IO): a synthetic patch release `(1,22,1)` with `body_changed=True,
  live_run_added=False` returns the same gap shape as an equivalent minor release. Commit
  `6a79d4b` (a skill-body fix) shipped with *no* version bump rather than a patch bump — a
  deliberate dodge of this exact gate, and itself weak evidence for which reading is right: the
  author's instinct under pressure was that the change didn't fit a patch number, not that the
  gate was wrong to apply.
- **options:**
  1. *The tool is too strict* — exempt patch releases in `evaluate()` to match §12's literal
     wording. Rejected: cheapest, but legalizes shipping skill-body changes under patch numbers
     indefinitely, which is what §12 exists to prevent (IMPROVEMENT_PLAN.md F4).
  2. *The doctrine is too lax* — reword §12 to "any release," keep the tool as-is. Rejected as
     disproportionate: it reads the minor/patch split as a granularity knob when it was always
     meant to gate substance, and would make a one-line skill typo fix owe a live run.
  3. *A skill-body change is semantically minor* **(chosen)** — the gate's uniform treatment was
     already right; the gap was §12 never saying so. SemVer's own rule (a behavior-changing
     release is never a patch) applies unmodified, since a skill body is this suite's behavior.
- **reversibility class:** two-way — a prose amendment and a docstring correction, no data
  migration; reversible by a future entry if a live run surfaces a genuinely patch-sized skill fix
  disproportionately blocked by this reading.
- **evidence tag:** **(proven)** for the tool/doctrine mismatch (executed against `evaluate()`,
  above); **(trace-only)** for which of the three readings is correct — the judgment call issue #4
  named as needing a ruling, not a code-derivable fact.
- **ruling provenance:** the director, asked directly which of the three readings to rule for,
  during this session's implementation of issue #4.
- **status:** decided — closed as option 3. `PROTOCOL.md` §12 and `cadence-check.py`'s docstring
  both restate "skill-body change ⇒ never a patch"; `tools/tests/test_cadence_check.py` gains a
  test pinning a patch-version skill-body change with no live run as a gap, so the ruling is
  enforced in code, not left for a reader to notice drift a second time.
