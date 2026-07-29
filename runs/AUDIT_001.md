# AUDIT_001 — External engineer audit of LIVE_RUN_004 (the first outside auditor)

PROTOCOL: 1.13.0 — vintage declaration (PROTOCOL §11, rule vintage). This transcript predates the sense floor (§11, added 1.16.0) and is linted by the rules it was written under; it is annotated, never retouched.

SUBJECT: top-tier-engineer-skill @ 26f11d2

> **Redacted for publication.** Subject systems appear as `SUBJECT_A` (a Flask + SQLite
> ticket-booking app), `SUBJECT_B` (a graph/memory service), and `SUBJECT_C` (a Next.js +
> Postgres time-tracker); local paths are removed. The redaction changes *identities only* —
> every finding, evidence tag, verdict line and file:line reference is the original. This is
> a publication edit, not a rules edit: PROTOCOL §11's "annotated, never retouched" governs
> retouching a transcript to satisfy a *check*, which nothing here does.

**What this artifact is.** The suite's roadmap names a pattern: *use top engineers as periodic
auditors to surface failure classes the suite cannot catch mechanically, then convert each finding
into a permanent check.* This is the first execution of that pattern. The director supplied an
external engineer's audit of LIVE_RUN_004 (the SUBJECT_C security review). This file records each
audit finding, its verification against the suite's own artifacts, and its disposition — the rule
and mechanical check it became. Per the honest-trace principle, **LIVE_RUN_004 is not retrofitted**;
it stands as written, and this ledger stands beside it.

**Evidence caps stated up front.** The SUBJECT_C repo is not reachable from this environment, so the
auditor's claims *about SUBJECT_C's code* (schema comments, `ledger.ts` intent notes, the hosted
`getProjectLedger` signature) are **(trace-only, auditor-attested)** here. What *is* independently
verifiable is the structural failure inside LIVE_RUN_004 itself — the run report is in this repo —
and every verification below was performed against that artifact directly.

---

## Finding A — Severity overstated: an imported invariant, contradicted by subject evidence in hand, was never reconciled

**Auditor's claim.** Invariant 1 ("entries visible only to owner / project members / admins") is
not SUBJECT_C's model: schema comments say "Everyone reads (analytics)", `fetchProjectLedger` is
documented gate-free by design, and the UI already shows any project's full ledger to any logged-in
teammate. The API hole grants an *insider* nothing new; the genuine risk is leaked-token blast
radius (tokens live outside the browser) plus the doc/model incoherence.

**Verification (proven, in-artifact).** LIVE_RUN_004 states its invariants were "derived from what
a shared time-tracker *is*" — a domain prior, i.e. an **imported** invariant. The *same report*
quotes `time_select = auth.role() = 'authenticated'` ("every authenticated user may read every
time-entry row") and F2's doc/code drift. The contradicting subject evidence was in the report's
own hands and was interpreted only as part of the defect, never tested as evidence of *intent*.
No reconciliation step existed anywhere in the suite for it to fail — the gap was doctrinal.

**Disposition.**
- **Baseline rule** added to `PROTOCOL.md` §1: a finding's consequence is measured as the *delta*
  over the subject's evidenced intent; subject evidence contradicting a derived invariant is
  reconciled before the invariant grounds any severity; an imported invariant contradicted by
  unrebutted subject evidence grounds none.
- `senior-review` Phase 1: invariants now carry provenance — **inherited / evidenced / imported** —
  and the reconciliation duty is stated at the derivation site.
- `threat-model` contract 7: openness-by-design is baseline, not finding; blast radius is computed
  against the evidenced baseline, and the finding, if any, is the residual delta (e.g. a credential
  class that travels differently).
- Mechanical reach: none — this is a semantic judgment no regex can gate. It is enforced at the
  two derivation sites plus the fresh-eyes pass (§8), which now has a named rule to check against.
  Logged honestly as the prose-only residue of this audit.

**Re-scored finding (what LIVE_RUN_004 should have said).** Not "insider confidentiality breach"
but: (1) leaked-token blast radius — any non-admin API token reads the whole company ledger from
outside the browser session; (2) intent incoherence — the declared model ("RLS enforces all
permissions") contradicts both the permissive RLS and the app-side ad-hoc scoping, which is what
made the hole invisible. Severity: real, but a tier below the original framing, with the asset
correctly named.

## Finding B — The delivered fix was never adjudicated, and it carried two incoherences

**Auditor's claim.** (a) Gating `exportEntries` by membership while the UI dialog still shows the
same rows to non-members is incoherent product behavior. (b) Membership is decorative in SUBJECT_C —
`tasks_write` is open to all authenticated users — so post-fix, someone actively working in a
project they were never formally added to cannot export it.

**Verification (proven, in-artifact).** LIVE_RUN_004 delivers a fix under "Law 5 — delivered, not
committed" *and* lists `scrutinize (no delta)` among not-applicable skills in the same report. The
fix was a delta; it went through no outsider pass; the two incoherences the auditor names are
exactly the class an outsider pass (surface enumeration + Chesterton's Fence on the gate predicate)
is built to catch. The (a)/(b) specifics are (trace-only, auditor-attested); the skipped
adjudication is proven here.

**Disposition.**
- **PROTOCOL §9 — delivered-fix discipline** added: a delivered fix is a delta (scrutinize binds,
  §8 fresh-eyes applies); surface parity must be enumerated; the gate predicate must carry
  authority evidence; every delivered fix closes with a `FIX <id>:` line
  (`coherent(surfaces: …) | incoherent(named: …) | unscrutinized`).
- Mechanical invokers (all tested, `tools/test_tools.py`, 22 green):
  `verdict-lint.py` lints the FIX form, **blocks** `coherent`/`incoherent` when no `SCRUTINY`
  verdict exists in the transcript, and requires the bold limitation marker on `unscrutinized`
  (the FIX analogue of a trace-only close).
- `scrutinize` wiring and `senior-review` Rule 5 / `threat-model` contract 6 now point to §9.

## Finding C — Line references and quoted signatures were floating evidence: no revision pin

**Auditor's claim.** The report's quoted two-arg `getProjectLedger(scope.projectId, svc)` does not
exist at the pushed GitHub revision (one-arg, internal client) — presumably a local post-v3 working
tree — and nothing in the report lets a reader tell which revision any quote was true of.

**Verification (proven, in-artifact).** LIVE_RUN_004 contains no commit id, no `SUBJECT` pin, no
dirty/local-only marker anywhere. The signature mismatch itself is (trace-only, auditor-attested)
— unverifiable from here, which is precisely the defect: *unresolvable ambiguity is the finding.*

**Disposition.**
- **Pin rule** added to `PROTOCOL.md` §1: every run report emitting verdicts carries
  `SUBJECT: <name> @ <revision>` (` +dirty` / ` local-only` when applicable, or
  `unversioned(<reason>)`); file:line references and quoted signatures are evidence at that
  revision only, and consumers at any other revision re-verify before acting — the decay rule
  applied to reading.
- Mechanical invoker: `run-trace.py` now refuses to mark **any classified run** complete without
  the pin (`TRACE: incomplete(…: missing SUBJECT)`), with a plain-language explanation a
  non-coder can act on. Tested both ways.

---

## What this audit proves about the auditor pattern

All three findings share one root: **the suite judged the subject against its own model of the
subject, and nothing forced that model to be pinned, evidenced, or adversarially checked.** The
pin rule fixes *which code* the model was built from; the baseline rule fixes *whose intent* it is
measured against; §9 fixes *who checks* the change it proposes. One external audit produced three
permanent rules and two mechanical gates — the conversion rate the roadmap hoped for. The
prose-only residue (Finding A's semantic reconciliation) is named above, not hidden.

`SCRUTINY: fix-then-ship(top: all three findings verified in-artifact; doctrine + tools patched; Finding A enforcement remains prose-only by nature)`
FIX AUDIT-001: coherent(surfaces: PROTOCOL §1/§5/§9, senior-review, threat-model, scrutinize, verdict-lint, run-trace, test_tools — all edited together, tested green)
