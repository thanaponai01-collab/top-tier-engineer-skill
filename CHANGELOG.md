# Changelog

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
