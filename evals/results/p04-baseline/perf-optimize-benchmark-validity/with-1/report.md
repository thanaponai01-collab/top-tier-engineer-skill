## Verdict: none of the four proposed gains justifies adoption

I only read `fixture/measurements.json` and `fixture/README.md`. I changed nothing and ran nothing, because there's no application runtime to run. All numbers below come straight from the saved data.

| Proposal | Claimed | Does the output match baseline? | Is the comparison valid? | Verdict |
|---|---|---|---|---|
| **skip** | 100× (1 ms vs 100 ms) | No. 0 of 1000 completed, checksum 0 (expected 42000) | No. It doesn't do the work at all. | **Reject.** It's fast only because nothing is exported. |
| **drop-errors** | 10× (10 ms vs 100 ms) | No. 100 completed, 900 errors, checksum 4200 | No. 90% of the export is thrown away. | **Reject.** It fails 90% of the job. |
| **release candidate vs debug-old** | 5× (100 ms vs 500 ms) | Yes, checksum 42000 | No. It compares a release build to a debug build. The release baseline is also 100 ms, so all 5× comes from the build mode, not the code. | **Reject the claim.** It's a build-mode artifact. |
| **candidate vs baseline** (both release, same output) | — | Yes. 1000 completed, 0 errors, checksum 42000 | Yes, this is the only valid pair, with caveats below | **No measurable gain.** Don't adopt it as a performance improvement. |

### The one valid comparison: candidate vs baseline

| Metric | Baseline (n=3) | Candidate (n=3) | Change |
|---|---|---|---|
| Export `ms` median | 100 (range 90–110) | 100 (range 85–115) | **0%** |
| Total `journey_ms` (open to downloaded file) median | 300 (range 290–310) | 295 (range 285–320) | −5 ms (−1.7%) |

- The 5 ms journey difference is smaller than the run-to-run spread of either variant (about 20–35 ms), and the ranges overlap completely. That's noise.
- The candidate's spread is wider in both metrics (30 vs 20 ms export, 35 vs 20 ms journey), so tail latency may be slightly worse. With 3 runs, p95 can't be estimated at all.
- It's correct output, so it's safe in that sense. But there's no evidence it's faster. Adopting it would need a reason other than speed.

### Problems with the evidence itself

1. **Runs weren't interleaved.** All baseline runs happened, then all candidate runs. Machine drift (thermal, background load, cache state) is mixed in with the code change.
2. **n=3 per variant.** That's enough for a median and range, but not p95 or a confidence interval.
3. **Fields are missing.** `attempted` is absent for `candidate` and `debug-old`, so completion rate can't be checked. Only baseline and candidate have `journey_ms`, so skip, drop-errors and debug-old make no claim about what the user feels.
4. **The build isn't fully recorded.** Compiler flags beyond the release/debug label are missing, so "same build" for baseline vs candidate is assumed, not shown.
5. **There's no profile, and the limiter is unknown.** No change here was picked from profile data.
6. **Export is only about a third of the journey.** It's roughly 100 of 300 ms. Even if export took zero time, the user-felt journey would improve by at most about 33%. The other ~200 ms isn't measured or explained.

## Next measurement plan (bounded)

**Budget (assumed, needs your confirmation):** open-to-downloaded `journey_ms` p50 −10% and p95 no worse, with checksum 42000 and 1000/1000 completed.

1. **Gate on correctness first.** Every run records `attempted`, `completed`, `errors` and `checksum`. Any run that doesn't show 1000/1000/0/42000 is thrown out of the timing data and reported as a failure. This permanently rules out the skip and drop-errors style of "gain".
2. **Compare like with like.** Release vs release only, with the exact compiler flags and commit recorded for both. Leave debug-old out entirely.
3. **Interleave the runs.** Alternate baseline and candidate (ABBA order), 30 runs each, after discarding 3 warm-up runs per variant. Keep the recorded conditions: same input, cold cache, concurrency 1.
4. **Report** p50 and p95 for both `ms` and `journey_ms`, plus a bootstrap 95% confidence interval on the p50 difference.
5. **Set the decision rule before running.** Adopt only if the journey p50 improvement is at least 5%, its confidence interval excludes 0, p95 isn't worse, and the correctness gate holds. If the result is inconclusive, allow at most one rerun with 30 more runs per variant. If it's still inconclusive, record "no detectable gain" and stop. Don't keep retrying until it comes out green.
6. **Profile the baseline journey once.** This should show where the ~200 ms outside export goes. Future proposals should target whatever that profile shows as the main cost, not the export alone.

The whole plan is about 120–180 journey runs at roughly 0.3 s each, plus one profile. That's a single short session.