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
| D-2 | `tools/graph-audit.py` :: `main()` | cyclomatic 16 (> 15), function_lines 88 (> 60) | CLI argument handling plus the four output modes, all linear and read top-to-bottom. Splitting a linear CLI entry point into helpers usually trades one long readable function for four short ones plus the burden of remembering their order. | Every new flag or output mode lengthens the one function a reader must hold in their head to know what the tool does. | Whichever comes first: a fifth output mode, or the next flag that is not a plain boolean. | 2026-07-27 |
| D-3 | `tools/structure-report.py` (whole file) | file_lines 626 (> 600) | **Newly breached by v1.15.0** (opacity signal + the ratchet), so this is a deliberate decision, not inherited debt. The obvious repair — splitting measurement, ratchet, and rendering into three more modules — costs the property that makes this tool adoptable: it is a stdlib-only entry point copyable into any repo with no install step. 26 SLoC over a threshold tuned to "a reviewer should look" does not outweigh that. Recorded rather than refactored, per §10 rule 2. **Partially repaid within the same version**: the opacity measurement moved out to `tools/structure_opacity.py`, which is why adding a whole new signal *lowered* the count from 638 to 626 — and the baseline was re-locked at the improved number, which is the only legitimate reason to regenerate one (§10 rule 3). | Every new signal adds to a file already over the god-file line, and the next reader has more to hold at once. | **700 SLoC.** At that point the portability argument no longer covers the size, and the file splits along its remaining seam: measurement (`analyze`) / ratchet (`apply_ratchet`, `signature_map`) / rendering (`print_human_report`, `json_report`). | 2026-07-27 |

## Repaid

*(none yet — when a row is repaid, move it here with the date and re-run
`--write-baseline` to lock the improvement in.)*

## Note on this repo's own history

Before v1.15.0 the `enforcement-floor` structural gate exited 1 on `main` because of D-1
and D-2, and had done so since those functions crossed threshold. A gate that is red for
reasons nobody is acting on is a gate people learn to scroll past — which is the practical
argument for the ratchet, demonstrated on the suite's own repository rather than asserted.
