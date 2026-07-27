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
| D-2 | `tools/graph-audit.py` :: `main()` | function_lines 77 (> 60) — *was 88; cyclomatic 16 repaid, see below* | CLI argument handling plus the four output modes, all linear and read top-to-bottom. Splitting a linear CLI entry point into helpers usually trades one long readable function for four short ones plus the burden of remembering their order. | Every new flag or output mode lengthens the one function a reader must hold in their head to know what the tool does. | Whichever comes first: a fifth output mode, or the next flag that is not a plain boolean. | 2026-07-27 |
| D-3 | `tools/structure-report.py` (whole file) | file_lines 626 (> 600) | **Newly breached by v1.15.0** (opacity signal + the ratchet), so this is a deliberate decision, not inherited debt. The obvious repair — splitting measurement, ratchet, and rendering into three more modules — costs the property that makes this tool adoptable: it is a stdlib-only entry point copyable into any repo with no install step. 26 SLoC over a threshold tuned to "a reviewer should look" does not outweigh that. Recorded rather than refactored, per §10 rule 2. **Partially repaid within the same version**: the opacity measurement moved out to `tools/structure_opacity.py`, which is why adding a whole new signal *lowered* the count from 638 to 626 — and the baseline was re-locked at the improved number, which is the only legitimate reason to regenerate one (§10 rule 3). | Every new signal adds to a file already over the god-file line, and the next reader has more to hold at once. | **700 SLoC.** At that point the portability argument no longer covers the size, and the file splits along its remaining seam: measurement (`analyze`) / ratchet (`apply_ratchet`, `signature_map`) / rendering (`print_human_report`, `json_report`). | 2026-07-27 |
| D-4 | `tools/test_tools.py` (whole file) | file_lines 604 (> 600) | **Newly breached by the v1.15.0 self-audit**, which added 7 tests (graph-audit layer coverage, the stop-gate code-loading guards, scanner-coverage UNKNOWN). **This row is what turned a red gate green, and that must be read as a §10 rule 4 withdrawal, not as rule 3 approving anything.** Rule 3 forbids moving the *baseline*; it says nothing against moving the *code*, and reducing a real measured value is repayment — the outcome the ratchet exists to produce. The defensible argument is rule 4, carrying capacity: this file's own repayment trigger (split per-tool behind `unittest discover`) came due with this increment, and deferring it by one increment is a withdrawal against the ledger, taken deliberately and priced below. It keeps the property CI depends on: one stdlib-only `python3 tools/test_tools.py` entry point with no test runner to install, the same argument that justifies D-3. | Every new tool test lands in a file already over the god-file line; the next reader loads all seven tools' fixtures at once to find one. | **The next test class added** — i.e. an eighth tool, or any tool needing its own fixture family. At that point the file splits per-tool (`test_structure.py`, `test_verdict.py`, …) behind a `unittest` discover entry point, and CI's single command becomes `python3 -m unittest discover tools`. | 2026-07-27 |

## Open withdrawals — the gate is RED and that is deliberate

*A withdrawal is §10 rule 4's second option: when a slice cannot pay down first, it "closes
naming the withdrawal." Naming it here is **not** acceptance — the baseline is untouched, so
`enforcement-floor` exits 1 until one of these is repaid. Regenerating the baseline to clear
this section would be §10 rule 3's forbidden move, and the section exists precisely so that
nobody is tempted to reach for it.*

| Withdrawal | Measured | Accepted | Why not repaid in this change | Repayment |
|---|---|---|---|---|
| W-1 | `tools/test_tools.py` file_lines **661** | 604 (D-4) | The v1.15.0 self-audit added 7 further tests binding the *verdict line and exit code*, not just report prose — the defect an outsider pass caught in the first round of fixes. D-4's own trigger ("the next test class added") is now plainly due, but splitting ~900 lines of tests per-tool is a purely mechanical change that deserves its own commit and its own review, not a tail-end edit inside an audit run. | Split into `tools/tests/test_<tool>.py` behind a `unittest discover` shim so CI's single `python3 tools/test_tools.py` command is unchanged. |
| W-2 | `tools/structure-report.py` file_lines **636** | 626 (D-3) | Net +10 SLoC for `build_verdict()`, which stops the tool emitting a bare `STRUCTURE: clean` over a subject whose deep signals never ran. D-3's stated trigger (700 SLoC) is not reached, so the portability argument still holds — but the ratchet binds the *increment*, not the trigger, and the increment grew. | Either fold into W-1's session, or take D-3's named seam (measurement / ratchet / rendering) if the file reaches 700 first. |

## Repaid

| ID | File / symbol | Signal repaid | How | Date |
|---|---|---|---|---|
| D-2a | `tools/graph-audit.py` :: `main()` | cyclomatic **16 → under 15** (gone from the source); `function_lines` **88 → 77** on the same function, still over threshold and still carried as D-2 | The layer-report rendering — five branches and their coverage arithmetic — moved out of `main()` into `print_layer_section()`. Forced by §10 rule 4, carrying capacity: a self-audit fix landed in `main()` and grew it 88 → 99, the ratchet went red, and paying down first was the alternative to re-baselining a regression (rule 3, the forbidden move). Net effect: a whole new coverage feature was added and the function came out *smaller than before it*. | 2026-07-27 |

## Note on this repo's own history

Before v1.15.0 the `enforcement-floor` structural gate exited 1 on `main` because of D-1
and D-2, and had done so since those functions crossed threshold. A gate that is red for
reasons nobody is acting on is a gate people learn to scroll past — which is the practical
argument for the ratchet, demonstrated on the suite's own repository rather than asserted.
