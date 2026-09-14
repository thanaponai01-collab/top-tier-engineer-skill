# Changelog

## 3.3.0 — 2026-09-14 — habits, not tone

- `How to answer` becomes `How to work`: seven engineering habits, each with a test that shows it was
  done. Understand before you change (trace the flow, reproduce, find every caller); ground truth over
  memory; decide what done looks like first; smallest change that holds (every changed line traces to
  the request); size the risk before the move; stop when you're guessing (two failed attempts on one
  idea means re-check the assumption); say how you know, briefly. Scaled to the stakes.
- The old tone rules (answer first, one question, disagree in one line, proven/traced/suspected) are
  folded into habits 1 and 7.
- `build-discipline` drops its "interfaces from ground truth" bullet: habit 2 now covers it.

## 3.2.0 — 2026-09-14 — the philosophy, applied to itself

- `How to answer` gains **Answer first** (every skill's report already opened with its verdict; two didn't)
  and **Say how you know** (proven / traced / suspected, defined once instead of in four skills).
- **Disagree in one line** no longer contradicts the skills that must stop: ask instead when a step
  can't be undone or would fake the result.
- `correctness-gate` and `structure-gate` reports now open with the verdict; `senior-review` ceiling
  mode asks at most one question.
- `structure-report.py` no longer names other skills. Removed `--debt-ledger` / `--require-debt-ledger`:
  the baseline and `repay_at` are the parts that catch regressions; the ledger was prose that drifted,
  and its default path made every `--baseline` run warn projects that never kept one.

## 3.1.0 — 2026-09-14 — the philosophy, back in every skill

- Each skill now opens with a `How to answer` section: the busy-senior-engineer stance from the old
  `PROTOCOL.md` §0, copied into every skill so each still stands alone.
- `tests/test_philosophy.py` fails if the copies drift apart.

## 3.0.0 — 2026-09-14 — independent skills, no governance

- Every skill now stands alone: no `PROTOCOL.md`, verdict lines, evidence-tag law, or hand-offs between skills.
- Removed the `boss` router and the always-on `meta-skills`.
- Merged overlapping skills: `reach-audit` → `wire-check`; `scrutinize` and `toptier-lens` → `senior-review`;
  `symptom-audit` → `perf-optimize`; `ship-gate` and `data-evolution` → new `safe-release`.
- Removed `agents/`, `runs/`, `DECISION_LEDGER.md`, `DEBT_LEDGER.md`, the structure baseline and the CI gates.
- `structure-report.py` and `graph-audit.py` now ship inside `structure-gate/scripts` and `latent-audit/scripts`.

Earlier history (1.x–2.15.0) is in git: `git show 7f1f2d6:CHANGELOG.md`.
