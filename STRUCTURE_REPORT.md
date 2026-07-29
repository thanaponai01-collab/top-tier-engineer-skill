# STRUCTURE_REPORT.md — latest structural measurement

Owner: `structure-gate` (PROTOCOL §3 registry). Companion artifacts: `.structure-baseline.json`
(the machine-readable freeze of accepted breaches) and `DEBT_LEDGER.md` (why each was accepted,
what it costs, and what makes repayment due).

**What this file is.** The result of the most recent `tools/structure-report.py` run over this
repository: coverage (§10 rule 5, the denominator), per-signal flags, and the ratchet result
against the accepted baseline. It measures *shape*, never wisdom — every flag routes to
`senior-review` / `scrutinize` for the judgment call (Law 3, violation ≠ deviation).

**Regenerate with:**

```
python tools/structure-report.py --baseline .structure-baseline.json --require-debt-ledger .
```

---

## Run — v1.17.0, 2026-07-29

`SUBJECT: top-tier-engineer @ c0dae0d +dirty` (the v1.17.0 design-audit delta, pre-commit)

**Coverage (§10 rule 5).** 8 code files scanned (8 Python, deep-analyzed; 0 other) · 152 functions · 2,437 code lines · **98.2% actually entered by a parser** · 43 lines opaque (inside
string literals) · 0 shallow (no parser for that language here) · 848 doc lines.

Everything below was measured over the entered portion **only**. The remaining 1.8% is
*unmeasured*, which is not the same as clean.

**Ratchet result.** Measured against 5 accepted breaches in the baseline:

- ✅ Every file carrying accepted debt is listed in `DEBT_LEDGER.md` (`--require-debt-ledger`).
- ✅ **HELD** — nothing got worse; known debt did not grow.

**Accepted breaches, and what moved this run.** Every one carries a `DEBT_LEDGER.md` row; a
baseline entry without one is amnesty, not acceptance, and fails the gate.

| Ledger ID | File / symbol | Signal (measured) | This run |
|---|---|---|---|
| D-1 | `tools/graph-audit.py :: build_graph()` | cyclomatic 21 | unchanged |
| D-2 | `tools/graph-audit.py :: main()` | cyclomatic 16 · function_lines 87 | **repaid back to baseline.** The §10.5 verdict fix first pushed it to 101 lines; `latent_verdict()` was extracted *before* the new behaviour was added (§10 rule 4, carrying capacity — in a file already on the ledger, the smallest diff is a withdrawal). |
| D-3 | `tools/structure-report.py` (whole file) | file_lines 626 | unchanged |
| D-4 | `tools/test_tools.py` (whole file) | file_lines 709 | **newly accepted.** Six regression tests, the §6 extraction-floor check and the D004 redaction gate crossed the god-file line; recorded with a cost and an 800-SLoC trigger rather than silently re-baselined (§10 rule 2). First written as 671, re-locked at 709 when the last gate landed — a first acceptance set to its true final value, not a re-baseline (there was no prior entry to overwrite). |

**Baseline regeneration, and why it was legitimate.** `.structure-baseline.json` was re-locked
this run. §10 rule 3 permits that only when debt is **repaid**, never to silence a regression —
re-baselining a red gate green is the one move that disables the ratchet. Both conditions were
checked against the *old* baseline before re-locking: the sole new entry was `test_tools.py` (a
recorded acceptance with a ledger row), `main()` moved 88 → 87 (an improvement), and no other
entry rose. Independently confirmed by the v1.17.0 `scrutinize` gate, which re-ran the ratchet
against the old baseline and reproduced `regressed(new: 1, worse: 0)` — nothing was raised to turn
a red gate green.

```
STRUCTURE: held(accepted: 5, repaid: 0)
```

---

## History

Per-release structural results before v1.17.0 are recorded in `CHANGELOG.md` under their release.

One note is kept here because it is this file's own failure mode. The v1.9.1 edition tracked a
single open finding — `tools/verdict-lint.py :: _check_sequence()`, cyclomatic 17 — and stated
that `enforcement-floor` "will report **red** on this one open, routed finding by design". That
function no longer exists, the gate has been green since the ratchet landed in v1.15.0, and the
five breaches that *are* real were absent from the page. The file was nonetheless carried forward
unchanged for eight releases and re-published verbatim during v1.17.0, where the `scrutinize` gate
caught it as a stale ledger asserting a false fact.

A ledger that ages silently is indistinguishable from one that is current, which is the same
defect class as a gate that cannot fail. Regenerate this file from a real run whenever the
structural shape changes — never edit its numbers by hand.
