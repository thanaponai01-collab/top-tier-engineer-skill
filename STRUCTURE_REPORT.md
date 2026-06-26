# STRUCTURE_REPORT.md — measured structural shape of the suite's own source

Owner: `structure-gate`. This is the handoff trail for the structural floor run against
the suite itself (the suite eats its own dog food). Every entry is **(proven)** — a real
measurement by `tools/structure-report.py` over real source. A finding is **review-needed**,
routed to `senior-review` for the wisdom call — never a condemnation (Chesterton's Fence,
suite Law 3, violation ≠ deviation).

## Run — v1.9.1 post-fix, 2026-06-26

Command: `python tools/structure-report.py .` → `STRUCTURE: findings(top: cyclomatic, count: 1) | review-needed` (exit 1). **(proven)**

| Signal | Location | Measurement | Disposition |
|---|---|---|---|
| Cyclomatic complexity | `tools/verdict-lint.py:112` `_check_sequence()` | complexity 17 (> 15) | **Open — routed to `senior-review`.** Unchanged from v1.8.0. |

**What changed from v1.9.0:** `tools/run-trace.py`'s `human_report()` (67 lines) tripped the long-function threshold on the first self-scan. As brand-new code in this commit (no Chesterton's Fence — same principle as v1.8.0's `structure-report.py` `main()` cleanup), it was split into `_format_stage_result()` (stage-check rendering) and the trimmed `human_report()` (header/footer + dispatch). Re-scan: the tool's own source is **clean**. The Unicode crash on Windows was also fixed in the same pass. Net result: count returns to 1 (the pre-existing `_check_sequence()` open item).

---

## Run — v1.8.0 install, 2026-06-26

Command: `python tools/structure-report.py .` → `STRUCTURE: findings(top: cyclomatic, count: 1) | review-needed` (exit 1). **(proven)**

| Signal | Location | Measurement | Disposition |
|---|---|---|---|
| Cyclomatic complexity | `tools/verdict-lint.py:109` `_check_sequence()` | complexity 17 (> 15) | **Open — routed to `senior-review`.** Not refactored. The function is a branchy state-machine over the §4 handoff chain (three sequence invariants); whether that density is justified or should be decomposed is a wisdom call this gate does not make. Left open on purpose. |

### Why this is recorded, not silenced
Per the `structure-gate` contract (measure, never judge): a threshold breach means *a
reviewer should look*, not *the author was wrong*. Auto-refactoring `_check_sequence()` to
drop it under 15 would be the tool stealing `senior-review`'s mandate — the exact overreach
the skill's boundary forbids. The breach stays visible until `senior-review` rules on it.

### Authoring note — `structure-report.py` itself
On first self-scan, `structure-report.py`'s own `main()` also tripped the gate (complexity 19,
108 lines). Unlike `verdict-lint` (pre-existing code, wisdom call reserved for `senior-review`),
that was brand-new code landing in the same commit — no Chesterton's Fence on code written
minutes ago — so it was cleaned at authoring: `main()` was split into `analyze()` (measurement)
and `print_human_report()` (rendering). Re-scan: the tool's own source is **clean**. This is
authoring hygiene, not gate-silencing; the distinction is provenance (new code cleaned vs.
existing code routed).

### Consequence for CI
`enforcement-floor` will report **red** on this one open, routed finding by design — the gate
hard-blocks on breach (its stated teeth) and the suite refuses to silence its own debt. The red
badge *is* the routing signal: it clears when `senior-review` rules on `_check_sequence()`.
