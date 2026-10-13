# P01 bounded evidence

2026-10-13, Asia/Bangkok. Local implementation committed on codex/p01-behavior-evidence. No skill instructions changed.

## Scope and mechanism

`evals/agent.py` now matches direct Read requests against existing staged skill files.
Skill-tool calls, matched reads (exact path and delegated flag), unvalidated SKILL.md candidates,
and the combined loading names are retained separately. Unrelated paths cannot count as staged
reads. Requested access is not proof of successful tool output or procedure compliance.
`evals/run.py` uses these records in loading reports and retains model usage and dispatch count.
Rescoring preserves validated reads only when their exact Read request still exists in the transcript.
Old runs without staging records remain uncertain; they are not silently counted as absent reads.
Executed rescore after staging cleanup: all four pilot results retain their verdicts and both
with-skill staged reads remain counted.

The historical recall discrepancy arose because the parser collected only Skill-tool calls;
the linked October 13 action log instead contains a direct staged Read. Historical artifacts
were preserved unchanged. The new live pilot reproduces that access path and correctly counts it.

## Repeated pilot

Command, executed twice (one pair each):

`python evals/run.py --cases recall-stale-proof --repeats 1 --jobs 1 --budget-usd 1 --timeout 240 --no-judge --no-scorecard --out evals/results/p01-pilot`

Raw transcripts, actions, reports, graders and metrics: [pilot summary](../../evals/results/p01-pilot/summary.json).

| Dimension | Without skill | With skill |
|---|---|---|
| Outcome | 2/2 pass | 2/2 pass |
| Loading requests | No Skill calls or SKILL.md reads | 2/2 exact staged recall Reads; no Skill calls |
| Procedure | Tests run and files preserved | Tests run and files preserved; full rubric unmeasured |
| Cost, reported list-price USD | 0.2611644 | 0.3978202 |
| Elapsed seconds | 16.7, 16.5 | 20.9, 28.3 |
| Worker dispatches | 0 | 0 |

Both arms identify the half-up constraint, unfinished --since work and two current test failures.
Retained action/tool output inspection confirms test execution and unchanged fixture files.
Outcome expectations are held outside the staged plugin/fixture. Phrase grading was used,
explicitly avoiding a paid semantic judge; the reports and action records were also inspected.
The case's command regex can match file-reading commands containing test_export, so that
regex alone is insufficient proof; full transcript inspection supplies the executed tests here.
No reliability or savings claim follows from these two small pairs. The with arm costs more here.

## Isolation and limits

Traced `build_command`, `clean_env`, `stage_plugin`, `one_run` and rescore. Fresh temporary
fixtures and plugin-only staging exclude eval answer keys. `--setting-sources project,local`
excludes installed user plugins/instructions; explicit manual recall invocation points to the
staged file. Environment is allowlisted; GitHub gets an empty config. These controls are not
a filesystem/credential security sandbox. No full matrix, recovery trial or model comparison ran.
Context token categories are retained in model_usage; exact bytes read are unmeasured.

## Helper proof

Regression first failed because parse_stream rejected plugin_dir; after implementation,
50 runner tests pass. It discriminates staged, unrelated, absent, unknown and delegated reads.
Full suite: 485 tests pass. A concurrent test edit invalidated the first Drive receipt despite
green tests; that rejection is retained in RUN.json and final-state checks are rerun.
Catalog check passes. RUN.json owns final execution status and receipts.

Next: add a bounded fixture with a full externally observed procedure rubric before claiming
procedure reliability. Larger fixtures and recovery remain outside this pilot's coverage.
