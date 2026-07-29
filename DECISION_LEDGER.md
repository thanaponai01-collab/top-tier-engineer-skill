# DECISION_LEDGER.md — the suite's own consequential decisions

Owner: `arch-design`. Append-only. Schema (PROTOCOL §3, arch-design §Record):
`ID | date | decision | options | forces | reversibility class | evidence tag | status`.
Superseding never deletes — future models need the archaeology. Every entry carries ≥2 options
and a reversibility class. Open questions live here as `status: open` until the director rules.

---

## D001 — Should observability be its own mandate, or stay folded into ship-gate + evolve-maintain?

- **date:** 2026-07-04
- **decision:** *(open — director decision)*
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
- **evidence tag:** (suspected) — no live run has surfaced an unowned observability finding yet.
- **status:** open — resolve when a live run either produces such a finding (→ option 2) or a
  ship-gate pass demonstrably covers it (→ option 1, close as folded).

## D002 — Should "taking a new dependency" be an owned decision, or stay in ponytail prose?

- **date:** 2026-07-04
- **decision:** *(open — director decision)*
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
  through the suite yet.
- **status:** open — resolve by either adding the arch-design checklist (option 1) or waiting for a
  live run to justify option 2.

---

*Provenance: D001/D002 opened by the v1.14.0 chief-engineer self-audit ("check the system, find the
gaps"). They record gaps the suite does not yet own, per PROTOCOL §4's rule that a missing mandate
is logged, not silently improvised. `DESIGN: blocked-on-director(one-way doors: none — both D001 and
D002 are two-way; director may defer both without cost)`.*

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
