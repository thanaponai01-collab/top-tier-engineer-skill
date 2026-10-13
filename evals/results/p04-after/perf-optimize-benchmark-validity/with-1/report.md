I reviewed `fixture/measurements.json`; there's no `measurements.json` at the top level. None of the four proposed gains justifies adoption. Three are invalid comparisons, and the fourth (candidate vs baseline) shows no difference that stands out from the noise. I worked only from the saved data: nothing was run, and the application wasn't changed.

## Each claim

Timings are median (range) of 3 samples. "Journey" is open-to-downloaded-file.

| Claim | Workload / config | Attempted / completed / errors / checksum (expected 42000) | Micro ms | Journey ms | Verdict |
|---|---|---|---|---|---|
| baseline | release, cold, concurrency 1 | 1000 / 1000 / 0 / 42000 ✓ | 100 (90–110) | 300 (290–310) | Valid reference |
| **skip "100x"** | release | 1000 / **0** / 0 / **0** ✗ | 1 (1–1) | not recorded | **Rejected.** It did no work: nothing completed and the checksum is 0. The 1 ms is the cost of doing nothing. |
| **drop-errors "10x"** | release | 1000 / **100** / **900** / **4200** ✗ | 10 (9–11) | not recorded | **Rejected.** 90% of requests failed and the output is wrong. Per successful invoice it costs 0.10 ms, the same as baseline (100 ms ÷ 1000). The "gain" is just 900 dropped invoices. |
| **release candidate vs debug-old "5x"** | debug vs release | attempted **missing** / 1000 / 0 / 42000 | 500 (490–510) vs 100 | not recorded for debug-old | **Rejected as a comparison.** It mixes the build mode with the code change, so the 5x is mostly or entirely the compiler. It also can't be fixed by applying a multiplier; it needs a release-vs-release run. The fair comparison is the next row. |
| **candidate vs baseline** | both release | attempted **missing** / 1000 / 0 / 42000 ✓ | 100 (85–115) vs 100 (90–110) | 295 (285–320) vs 300 (290–310) | **Inconclusive, no gain shown.** The micro medians are identical. The journey medians differ by 5 ms (1.7%), well inside the ±10–20 ms spread, and the candidate's range is wider. |

## Problems with the data

- **Run order is confounded with the variant.** The data says "baseline batch then candidate batch", so any drift in cache, thermal state or background load lands entirely on one variant. Cold cache with only 3 runs each makes that worse.
- **3 samples per variant** are too few for anything beyond a rough median. No p95 or tail claim can be made.
- **Attempted counts are missing** for candidate and debug-old. Completed = 1000 and the correct checksum suggest no requests were dropped, but that isn't proven.
- **Compiler flags beyond the "release"/"debug" label weren't recorded**, so even baseline vs candidate isn't confirmed to use the same build configuration. Hardware and dependency versions aren't recorded either.
- **There's no profile**, and the candidate's limiter (the constrained resource: CPU, I/O, network, lock) is unknown. There's no stated mechanism for why the candidate would be faster, so there's no predicted size to test against.
- **There's no adoption target.** The owner hasn't stated a threshold, so I haven't invented one. The plan below needs one before its run.

## Decision

- **Adopt:** nothing on performance grounds.
- **Reject:** skip, drop-errors and the debug-vs-release comparison. Their numbers should not appear in any summary of the gain.
- **Candidate:** inconclusive. It is correct (checksum ✓), but there's no evidence it's faster. If it has other merits it can be judged on those, but not as a speedup.

## Next measurement plan (bounded)

The goal is a single experiment that settles candidate vs baseline.

1. **Pin the setup.** Same machine, record the hardware, identical release flags (capture the full compiler and linker command for both builds), same dependency lockfile, and the same 1000-invoice input. Record the artifact hashes.
2. **Set the target before running.** The owner names a target, for example "journey p50 improves by at least X ms". If they don't give one, label any threshold used as an assumption, not a goal.
3. **Interleave the runs.** Use alternating order (ABBA ABBA …), 20 runs per variant. A journey takes about 0.3 s, so the total is about 15 s of timed work plus the cache reset. Apply the same cold-cache reset before every run and log run order and index. If the spread is still ±10 ms or more after 20 runs, report the result as inconclusive. Don't keep extending the run until it shows a gain.
4. **Check correctness on every run.** Record attempted, completed and errors, and require checksum = 42000. Any run that fails counts as a failure; don't drop it from the dataset.
5. **Report the results.** Give the median and interquartile range (IQR) for both micro and journey times, plus the paired difference and the variation between adjacent baseline/candidate pairs. Report p95 only if 20 samples clearly support it; otherwise say they don't.
6. **Profile separately.** Do one profiled run of each variant to identify the limiter and explain any difference. Don't use the profiled runs for timing.
7. **Stop rule.**
   - **Adopt** if the journey gain clears the stated target and exceeds the paired variation.
   - **Reject** the speed claim if it doesn't.
   - **Re-scope or drop** if the micro step is only a small part of the 300 ms journey. In this data the export takes about 100 ms of the 300 ms, and the rest is outside it.

If the candidate is adopted, add a guard that fails if the journey p50 slips back above the baseline.