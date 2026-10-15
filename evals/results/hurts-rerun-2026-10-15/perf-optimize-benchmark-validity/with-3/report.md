I followed the perf-optimize skill and its benchmark-validity rules. Only saved data was provided (`fixture/measurements.json` and its README), so this is analysis only. Nothing was run and nothing in the app was changed.

## Verdict: adopt none of the proposed gains

| Proposed gain | Data | Verdict |
|---|---|---|
| **skip (100×)** | median 1 ms vs 100; **0 of 1000 completed**, checksum 0 (expected 42000) | **Rejected.** It does no work, so this isn't a speedup. |
| **drop-errors (10×)** | median 10 ms; **100 of 1000 completed, 900 errors**, checksum 4200 | **Rejected.** The output is wrong and 90% of runs fail. Per completed unit it costs about 0.10 ms, which is what the baseline costs (100 ms / 1000). Per unit of useful work there is no gain at all. |
| **release candidate vs debug-old (5×)** | 500 ms (debug) vs 100 ms (release) | **Rejected as an invalid comparison.** Debug vs release measures the build mode, not the code. The fair comparison, release vs release, is the next row, and it shows 1×. `debug-old` is also missing its `attempted` count. |
| **candidate vs baseline (release vs release)** | see below | **Inconclusive.** No gain shows above the noise. |

**Candidate vs baseline in detail** (same input, cold cache, concurrency 1, n=3 each):

| | Baseline | Candidate |
|---|---|---|
| Export median (range) | 100 ms (90–110) | 100 ms (85–115) |
| Journey median (range) | 300 ms (290–310) | 295 ms (285–320) |
| Correctness | 1000/1000, 0 errors, checksum 42000 ✔ | 1000 completed, 0 errors, checksum 42000 ✔; **`attempted` missing** |

The candidate's output looks correct. The 5 ms journey difference (about 1.7%) is well inside the overlapping ranges, and the export medians are the same. The candidate's spread is also wider, so it may have higher variance; that's suspected, not shown.

## What weakens the candidate comparison
1. **Order confound:** all baseline runs came first, then all candidate runs. Drift (thermal state, background load, disk cache) can't be separated from the code change.
2. **Too few samples:** 3 runs each gives a median and a range. Nothing can be said about p95 or tails.
3. **Configuration not fully recorded:** compiler flags beyond the "release" label, hardware and dependency versions are missing.
4. **Missing `attempted` count** for the candidate (and for debug-old), so completion rate can't be confirmed.
5. **No target and no profile:** nobody stated an adoption threshold, there's no profile to show where time goes, and the candidate's limiter (CPU, I/O, etc.) is unknown.

## Next measurement plan (bounded; not run)
Scope: baseline vs candidate only, both release builds from the same toolchain. skip and drop-errors stay rejected until they pass the checksum.

1. **Target (needs the owner's sign-off):** without one, I'd propose adopting only if the journey p50 improves by at least 10% (about 30 ms) with no correctness regressions. If the owner won't set a target, the result can't be more than "no measurable difference."
2. **Record conditions once:** commit/artifact hash, full compiler flags, hardware, dependency versions, cache policy (cold), concurrency 1.
3. **Alternate runs:** A B B A … for 15 pairs (30 runs), clearing the cache before every run, with one discarded warm-up per variant. Run order is kept with the results. Why 15: the observed spread is about ±10 ms on a 100 ms median. Detecting a 10% shift in paired runs at that noise needs roughly 15 pairs. At about 0.3 s per journey, the whole session is under a few minutes.
4. **Per run, record:** attempted, completed, errors, checksum (must equal 42000), export ms and journey ms. Any run with the wrong checksum or with errors is reported, not filtered out.
5. **Decision rule:**
   - **Adopt** if the median of paired journey differences meets the target and the paired differences consistently favour the candidate.
   - **Inconclusive, keep baseline** if the difference is within run-to-run spread. Don't add more runs just to get a pass.
   - **Reject** if correctness or the candidate's spread gets worse.

   Report p50 only; 15 samples isn't enough for p95.
6. **Profile separately** (not during timed runs) to find the candidate's limiter. If a gain is adopted later, add a regression guard: a journey-time budget check that fails at the agreed threshold.

**Bottom line:** two of the four proposals are fake speedups, one compares build modes rather than code, and the only valid comparison shows no measurable gain. Nothing justifies adoption yet. The 15-pair alternating run above will settle the candidate question within a few minutes of runtime.