# LIVE_RUN_003 — The suite, run against itself

**Subject:** this suite, v1.6.1 (seventeen skills + PROTOCOL + tooling).
**Mode:** read-only, full-lifecycle self-audit. `(same-context review)` — the audit was run in
the session that also wrote the v1.6.2 fixes, so per PROTOCOL §8 every verdict below is marked
accordingly and weighed down one tier where it bears on the author's own work.
**Why this run is different from 001 and 002:** those ran the suite against *other people's* code
(a Flask app; the Tier-Memory system) and proved the suite **finds bugs**. This run turns the
suite on itself and tests a different claim — whether the suite's own doctrine survives its own
discipline. It does, with four findings, all now fixed in v1.6.2.

---

## What was run, and what each skill found

The honest result of "run all skills against a doctrine repo" is that **ten skills bound to a real
subject and seven correctly returned not-applicable** — a markdown suite has no slices to build, no
queries to cost, no trust boundary, no release, no schema, no observed failure. Forcing a verdict
where there is no subject would itself violate Law 3 (violation ≠ deviation) and Discipline 1
(calibration). The empty returns are a pass, not a skip.

### The ten that bound

- **problem-framing** → `BRIEF: ready(reconstructed, trace-only)`. The suite frames everyone's
  project but was never framed as one. Reconstructing its implicit brief surfaced the finding that
  one invariant — Law 6, "constrain process, never intelligence" — had **no acceptance criterion**
  and so was the one rule in the suite that couldn't be tested. **Fixed (F2).**
- **arch-design** → `DESIGN: ready(trace-only)`. Shape is sound; the one real observation was that
  `PROTOCOL.md` is a single point of failure by design and the degradation story (§6) covered only
  the evidence tags, not the Laws or registry. **Fixed (F1).**
- **senior-review** → `REVIEW: shippable-with-findings(no enforcement floor)`. Confirms the
  standing residual risk: the laws bind only a cooperative model; the sole mechanical check
  (`verdict-lint.py`) validates verdict-line *grammar*, not the truth of claims. **Not fixed —
  this is the real ceiling**; the honest fix is CI/branch-protection, deferred, now recorded as the
  driver for the next run rather than papered over.
- **scrutinize** → `SCRUTINY: fix-then-ship(model-agnostic thesis is asserted, never tested)`. The
  five "Why this skill improves as models improve" sections are **(suspected)** by the suite's own
  vocabulary — nothing measures whether a stronger model does better through the same contract.
  **Addressed (F3):** the thesis is now explicitly tagged (suspected) suite-wide with a named
  experiment to settle it (below), and Law 6 gained a per-skill checkable proxy (the substitution
  test).
- **symptom-audit** → `AUDIT: prescribed(1 phase, top: gloss covers only vocabulary)`. Pinned the
  felt complaint "a skill pulled out of the suite silently loses 90% of its law," traced it through
  §0 → §6, prescribed the bounded fix. **Fixed (F1).**
- **data-tier** → `DATATIER: clean(no data access)`. Correctly empty.
- **verdict-lint (tooling)** → **(proven)**: lints clean on 001/002, correctly reports "no verdict
  lines" on governance files. The finding *is* the result — exactly one component in the suite can
  mechanically verify anything, and only grammar.
- **meta-skills** bound as the lens (every verdict above carries its tag, leads with bad news,
  names its tradeoff) rather than as a subject.
- **build-discipline / wire-check** → bounded to the only analog available: the README's "zero
  orphans" claim, `(trace-only: every skill appears in chief-engineer's routing table)`.

### The seven that correctly returned not-applicable

`correctness-gate` (no executable behavior → no oracle), `debug-protocol`
(`CAUSE: unreproduced` — no observed failure; the skill refuses to debug a non-failure),
`perf-optimize` (nothing runs), `evolve-maintain`, `threat-model`, `ship-gate`, `data-evolution`
(no incident, no trust boundary in prose, no release, no schema). Each returning *empty* rather
than *forced* is the suite practicing Law 3 on itself.

---

## Why the convergence is the strongest evidence here

The prior single senior-review *asserted* "no enforcement floor." This run reaches the same root
cause from **five independent lenses**: problem-framing finds the unfalsifiable invariant,
arch-design finds the thin degradation, scrutinize finds the untested central thesis,
symptom-audit finds the law-loss-on-extraction, and four skills return empty because there is
nothing executable to enforce against. One root cause surfacing through five different contracts is
worth more than one reviewer asserting it once.

---

## Subtraction pass (Discipline 7)

One genuine candidate: `scrutinize` and `senior-review` share ~60% of their machinery. The split
(delta-scoped vs codebase-scoped) is documented from both sides and currently pays rent, so the
verdict is **keep, but watch** — recorded now as a boundary watch-item in both wiring blocks
(F4). Everything else passed the no-redundancy test cleanly.

---

## The experiment that would settle the model-agnostic thesis (designed, not yet run)

The suite's reason to exist — *a stronger model inside the same contract produces strictly better
results* — is its least-tested claim. This is the spec for the run that would move it from
**(suspected)** to **(proven)**. It is recorded here as an artifact (Law 2) so any future session
can execute it without this conversation.

**Design — the two-tier substitution test:**

1. **Fix the contract, vary the model.** Pick one skill with an executable subject (e.g.
   `correctness-gate` or `debug-protocol`) and one fixed task with a known-good answer (reuse the
   LIVE_RUN_001 Flask defects — ground truth already established).
2. **Two arms, identical inputs:** run the *same* SKILL.md, the *same* task, the *same* artifacts
   under (a) a weaker model tier and (b) a stronger model tier. Nothing varies but the model.
3. **Pre-registered metrics**, written before either run so neither can be rationalized after:
   defects found / ground-truth defects (recall); false findings (precision); proportion of claims
   that reach **(proven)** vs cap at **(trace-only)**; whether the stronger arm's verdict line is
   strictly more informative under the same grammar.
4. **The falsifier, stated up front:** the thesis *fails* if the stronger model does **not** score
   strictly better on recall-at-equal-precision through the unchanged contract — i.e. if the skill
   either caps the stronger model (a Law 6 violation hiding as a ceiling) or fails to lift the
   weaker one (the contract isn't actually constraining process). A null result is a real result
   and edits the suite.
5. **Cost guard:** two arms × one skill × one task is a bounded run; resist expanding to all
   seventeen before the method is proven on one.

Until this runs, the per-skill proxy is the **substitution test** now written into Law 6: strip
every concrete instance from a skill; if what remains still fully specifies the work, the skill
constrains process rather than encoding knowledge. That proxy is **(trace-only)** and checkable by
reading today; the two-tier run above is what makes the thesis **(proven)**.

---

## Verdict

`REVIEW: shippable-with-findings(top: the model-agnostic thesis — the suite's reason to exist — is
its least-tested claim; v1.6.2 makes it falsifiable and specifies the run that would prove it, but
does not yet run it) | (same-context review)`

Residual risk after v1.6.2, stated honestly: the enforcement floor is still prose, not mechanism.
The four fixes here are **(trace-only)** — they are better words, exercised by no run. The next
edit to these files should be driven by either the two-tier experiment above or a CI hook that
makes one law mechanical — not by further design.
