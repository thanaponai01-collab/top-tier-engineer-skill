# P04 benchmark validity — bounded evidence

User authorized local P04 implementation on 2026-10-13. No release or installed-plugin update.

Implementation: perf-optimize opens references/benchmark-validity.md for measurement decisions and
saved-data reviews. The reference owns workload, useful work/errors/output checks, comparable builds,
alternation, variation, journey, limiter, separate profiling and bounded sampling requirements.

## Trials
- Baseline: evals/results/p04-baseline; with and without both phrase-pass 5/5.
  With report prescribed 30 runs and invented thresholds. No baseline outcome failure demonstrated.
- First change: evals/results/p04-after; with 4/5, without 5/5.
  With rejected zero completed work but phrase scorer missed “nothing completed”.
  It still prescribed 20 runs without variability-based sizing.
- Stronger loading pointer: evals/results/p04-replay; with 4/5.
  Transcript shows reference read; report rejects skip, 900 errors and debug/release,
  labels candidate inconclusive and retains journey/spread, missing counts/config and limiter.
  Scorer again misses correct zero-work rejection. Full sampling uses spread/target, but the
  arbitrary 20-pair pilot remains a procedure gap. No third retry on this instruction approach.

All trials used harness defaults, one job, 180-second timeout, $2/run cap and phrase grading.
Total recorded cost $0.92; single trials cannot establish reliability or comparative savings.
No runtime supplied: saved measurements were analysed, not independently collected or profiled.
The oracle’s must_read field is unsupported by this harness; loading assessed from actual actions,
not that field. Read-only changes are enforced. Five report findings are phrase-graded; sampling,
limiter and reference loading require manual transcript/report inspection.

## Verification and next
Existing grader tests pass (44); good/bad reference reports discriminate. Final repository run: 494 tests passed in 100.250 seconds; catalog and diff checks pass.
The earlier BUILD.md length failure was corrected; RUN.json retains the failed check.
RUN.json records failed acceptance for the sampling procedure gap, not a code-test failure.
Context handoff check reports two existing gaps (p02/trials and illustrative packages/auth/VERIFY.md).
Next: discriminate sampling-budget compliance explicitly in a future independently observed trial;
P04 implementation is present, but full procedural acceptance remains partial.
