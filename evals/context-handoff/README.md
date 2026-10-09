# Two-session context handoff

2026-10-09. Two independent agents were started with no inherited conversation. The first read
problem-framing and build-discipline, received a mid-build owner change to tenant-separated JSON,
and maintained the project notes. The second receives only the saved workspace and recall skill,
with the request to explain the goal, state and next step. Its capsule is in reader-report.md.

The input had 35 active auditing decisions, an old CSV decision and 200 historical entries.
The first attempt correctly refused to archive unsupported history. The corrected fixture used
200 actual repetitions of `python check.py`, with product files committed inside the fixture at
8e5b17c. This is a synthetic history-volume test, not 200 independent features. The writer replayed
the check and confirmed the committed baseline before archiving the receipts verbatim.

The owner change requires JSON groups per tenant containing invoice_id and amount. Product code
and its green check deliberately still implement CSV. A correct fresh reader must preserve the
JSON intent, identify the mismatch, avoid treating the CSV check as JSON proof, and propose a
requirement-backed next check. The live email credential blocker must survive compaction.

Replay saved-artifact checks: `python evals/context-handoff/check_artifacts.py`.
All 35 active decisions, 200 receipts, current intent and the blocker survived; budgets passed.
A scratch copy with Area 0 removed was rejected as `active decisions lost`.

The separate existing live regression is saved in `evals/results/context-handoff-regression/`:
one with-skills run passed using the phrase grader plus finished-workspace checks, costing $0.20.
No semantic judge was used. These runs are evidence for these fixtures, not a reliability estimate.

Fresh-reader outcome: recovered tenant-separated JSON, invoice fields, all auditing areas and the
credential blocker; identified the still-CSV implementation and limited its passing check to that
baseline; proposed retaining a failing JSON requirement check before implementation. It read current
area notes and left both archives unread. BRIEF.md was 26 lines and BUILD.md 19, with no budget overruns.
This was one independent writer/reader pair, not a repeated multi-agent reliability study.

`baseline.bundle` preserves the test-only committed product baseline. The embedded fixture `.git`
was moved out after evaluation so the evidence can be tracked normally. For Git-based replay,
clone the bundle into a temporary folder, then copy the saved notes into that clone. Run `python
-B check.py` there. The capsule's Git observations describe the evaluation-time workspace.
