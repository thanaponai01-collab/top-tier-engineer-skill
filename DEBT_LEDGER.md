# DEBT_LEDGER.md — accepted structural debt

Owner: `structure-gate`. Schema and obligation: `PROTOCOL.md` §3 (registry) and §10 (the
ratchet rule). Companion artifact: `.structure-baseline.json`, the machine-readable freeze
of the same breaches.

**What this file is.** Every structural breach this project has looked at and *accepted*.
Acceptance is not absolution — it is a recorded decision with a price and an expiry. A
breach in the baseline but absent from this table is amnesty, not acceptance, and
`structure-report.py --require-debt-ledger` fails the run for it.

**What this file is not.** A backlog of things that would be nice to clean up. Every row
must name what it costs *every future change that touches it* and the **trigger** that makes
repayment due — a deferral with no trigger is a wish (`TODO_LEDGER.md`'s rule, applied to
structure).

**The one forbidden move.** Regenerating the baseline to turn a red gate green. A baseline
is regenerated when debt is **repaid**, never to silence a regression (§10 rule 3) — that is
the structural analogue of weakening a proof line to pass it, and it is the single action
that disables the ratchet.

| ID | File / symbol | Signal (measured) | Why accepted | Cost per future change that touches it | Repayment trigger | Date |
|---|---|---|---|---|---|---|
| D-1 | `tools/graph-audit.py` :: `build_graph()` | cyclomatic 21 (> 15) | The function is one dispatch over the distinct reference kinds the import/reference graph must recognise (imports, from-imports, attribute references, raw-text rescues). The branch count *is* the enumeration; flattening it into helpers would scatter one closed set across four call sites and make the "did we cover every reference kind" question unanswerable by reading. Law 3, violation ≠ deviation. | Every new reference kind adds a branch here and cannot be tested in isolation from the rest of the dispatch. | The next reference kind added after Python — i.e. the first non-Python language `graph-audit.py` must parse. At that point the dispatch becomes per-language and needs a real table. | 2026-07-27 |
| D-2 | `tools/graph-audit.py` :: `main()` | cyclomatic 16 (> 15), function_lines 87 (> 60) | CLI argument handling plus the four output modes, all linear and read top-to-bottom. Splitting a linear CLI entry point into helpers usually trades one long readable function for four short ones plus the burden of remembering their order. | Every new flag or output mode lengthens the one function a reader must hold in their head to know what the tool does. | Whichever comes first: a fifth output mode, or the next flag that is not a plain boolean. | 2026-07-27 |
| D-3 | `tools/structure-report.py` (whole file) | file_lines 626 (> 600) | **Newly breached by v1.15.0** (opacity signal + the ratchet), so this is a deliberate decision, not inherited debt. The obvious repair — splitting measurement, ratchet, and rendering into three more modules — costs the property that makes this tool adoptable: it is a stdlib-only entry point copyable into any repo with no install step. 26 SLoC over a threshold tuned to "a reviewer should look" does not outweigh that. Recorded rather than refactored, per §10 rule 2. **Partially repaid within the same version**: the opacity measurement moved out to `tools/structure_opacity.py`, which is why adding a whole new signal *lowered* the count from 638 to 626 — and the baseline was re-locked at the improved number, which is the only legitimate reason to regenerate one (§10 rule 3). | Every new signal adds to a file already over the god-file line, and the next reader has more to hold at once. | **700 SLoC.** At that point the portability argument no longer covers the size, and the file splits along its remaining seam: measurement (`analyze`) / ratchet (`apply_ratchet`, `signature_map`) / rendering (`print_human_report`, `json_report`). | 2026-07-27 |

| D-4 | `tools/test_tools.py` (whole file) | file_lines 709 (> 600) | **Newly breached by v1.17.0**, which added six regression tests (rule-vintage inheritance, the LATENT profile, the §10.5 denominator), the §6 extraction-floor check, and the D004 redaction gate. **The figure was first recorded at 671 and re-locked at 709 within the same release**, when the redaction gate landed after the ledger row was written. That is a first acceptance being set to its true final value, not a §10 rule 3 re-baseline: `test_tools.py` had no prior baseline entry to overwrite, so no earlier measurement was raised to turn a red gate green. Any growth from 709 onward is a genuine regression and must fail. A test suite grows monotonically with the number of rules it enforces — that growth *is* the enforcement floor widening, and shrinking it by testing less is the one repair that would be a defect. The obvious split (a `tests/` package, one module per tool) costs what D-3 costs: CI invokes this as a single stdlib entry point, `python3 tools/test_tools.py`, with no install step and no test runner to configure. Recorded rather than refactored, per §10 rule 2. | Every new tool rule adds to a file already over the god-file line; a reader looking for one tool's tests scrolls past six other suites to find them. | Whichever comes first: **800 SLoC**, or the first fixture that must be shared across two tool suites (at that point a package with a shared setup earns the import wiring it costs, and the file splits one class per module). | 2026-07-29 |
| D-5 | `tools/registry-check.py` :: `main()` (stdout/stderr reconfigure block) | 6-line block duplicated with `tools/stop-gate.py:196` | **Newly breached by v1.18.0.** A fresh-eyes `scrutinize` gate on the delivery caught `registry-check.py` crashing with `UnicodeEncodeError` under a non-UTF-8 stdout — every other CI-gating tool (`structure-report.py`, `verdict-lint.py`, `stop-gate.py`) already guards its own output stream, and this one was the exception. The fix is the same `for stream in (sys.stdout, sys.stderr): reconfigure(...)` block `stop-gate.py` already carries, copied rather than imported: each tool in `tools/` is a standalone stdlib-only script, deliberately copyable into a consuming repo with no import wiring back to this suite (the same portability argument `registry-check.py`'s own module docstring makes for why it does not import `verdict-lint.py`). A shared `_encoding.py` helper would remove the duplication but break that property for both files. | Every future tool that needs UTF-8-safe output copies the same 6 lines rather than importing a shared helper; a reader scanning for the "real" version of this fix has three copies to compare instead of one. | The fourth tool that needs this guard. At that point three independent copies is pattern, not portability, and it earns a shared helper — `tools/_encoding.py` — that all three import, with the standalone-copy guarantee re-scoped to "vendor two files, not one." | 2026-08-02 |

## Repaid

| ID | File / symbol | Was | Repaid how | Date |
|---|---|---|---|---|
| — | `tools/graph-audit.py` :: `main()` | function_lines 88 → 101, cyclomatic 16 → 18 during v1.17.0 | The §10.5 verdict fix landed inside `main()`, a function already carrying accepted debt (D-2). §10 rule 4, carrying capacity: in a file on the ledger the smallest diff is a withdrawal, so the logic was extracted to `latent_verdict()` **before** the new behaviour was added. `main()` came back to **87** lines — one under the 88 it started at, which is why the baseline was re-locked at 87 and D-2's row above now reads 87. The ratchet caught this on the suite's own increment, the first time it has done so. D-2 itself remains accepted and unrepaid. | 2026-07-29 |

## Note on this repo's own history

Before v1.15.0 the `enforcement-floor` structural gate exited 1 on `main` because of D-1
and D-2, and had done so since those functions crossed threshold. A gate that is red for
reasons nobody is acting on is a gate people learn to scroll past — which is the practical
argument for the ratchet, demonstrated on the suite's own repository rather than asserted.
