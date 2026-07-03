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
