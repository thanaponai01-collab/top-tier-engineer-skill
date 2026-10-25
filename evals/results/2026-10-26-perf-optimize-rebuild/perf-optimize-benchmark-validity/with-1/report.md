I followed the skill's rule for saved data with nothing to run: I judged `fixture/measurements.json` against its benchmark-validity reference. No application or runtime was supplied, so **I ran no timings or profiles**, and the `perf.py` gate needs runnable code, so I didn't use it either. No files were changed.

## Verdict: none of the proposed gains justifies adoption

| Variant | Work done / errors / checksum | Timing (median, range) | Verdict |
|---|---|---|---|
| baseline (release) | 1000 of 1000 done / 0 errors / 42000 ✓ | 100 ms (90–110); journey 300 ms (290–310) | Reference |
| **skip** ("100x") | **0 of 1000** / 0 errors / **0 ✗** | 1 ms | **Rejected.** No work was done, so the speed means nothing. |
| **drop-errors** ("10x") | **100 of 1000** / **900 errors** / **4200 ✗** | 10 ms (9–11) | **Rejected.** 90% of the work failed and the output is wrong. Per successful invoice it is 0.10 ms, the same as baseline (100 ms ÷ 1000), so there is no gain even on that basis. |
| **debug-old → candidate** ("5x") | 1000 done / 0 errors / 42000 ✓; **attempted count not recorded** | 500 ms vs 100 ms | **Invalid comparison.** It compares a debug build with a release build. Release baseline is already 100 ms, so the whole 5x comes from the build mode, not from code. |
| **candidate vs baseline** | 1000 done / 0 errors / 42000 ✓; **attempted count not recorded** | 100 ms (85–115) vs 100 ms; journey 295 ms (285–320) vs 300 ms | **Inconclusive.** The medians are equal and the ranges overlap completely. The candidate spreads more (standard deviation about 15 ms vs 10 ms). The 5 ms journey difference is well inside the noise, and the means are both 300 ms. |

## Problems and uncertainty in the saved data

- **Batched order.** All baseline runs came first, then all candidate runs. That mixes up drift (thermal, background load, cache state) with the change itself. The runs need to be alternated.
- **Only 3 samples per variant.** Nothing can be said about tail latency (p95/p99), and even the median is shaky.
- **Missing configuration.** Compiler flags beyond the "release"/"debug" label, hardware, dependency versions and resource limits aren't recorded. That makes the "release" runs only *labelled* comparable, not shown to be.
- **Candidate didn't record `attempted`.** Its 1000 completions and correct checksum are encouraging, but per the validity rules unknown counts block adoption on their own.
- **No profile and limiter unknown.** Nothing shows what the candidate targets (CPU, I/O, lock, etc.), so the reason it should be faster is unproven.
- **No adoption target stated.** I haven't invented one. Note that the timed export is about 100 ms of a roughly 300 ms journey, so any export gain can save the user at most those same milliseconds.

## Next measurement plan (bounded)

1. **Pin the setup.** Use one machine and record the exact release artifacts for baseline and candidate, their full compiler flags, dependency versions, hardware, cache policy (stay with cold cache, reset before every run) and concurrency 1. Ask the owner for the smallest gain worth adopting.
2. **Check every run.** Record attempted, completed and errors, and require checksum = 42000. Any failed run is reported, not dropped.
3. **Alternate the runs.** Run baseline and candidate in randomized pairs, about **30 pairs** each for the export and for the open-to-downloaded-file journey. Fix that count before starting, and don't retry until it looks good. At the observed noise (about 12–13 ms standard deviation), 30 pairs can reliably detect a difference of roughly 9 ms. Detecting 5 ms would take about 100 pairs. Each run is about 0.3 s plus the cache reset, so this costs minutes. Pick the size from the owner's target.
4. **Report** the median, interquartile range and pairwise difference with a confidence interval for both the export and the journey. Report p95 only if there are enough samples. Report the run order too.
5. **Profile separately.** Do one profiled run each of baseline and candidate, outside the timed runs, to name the limiter and confirm the change targets real hot time.
6. **Decision rule.** Adopt only if the work is complete and correct, the configuration matches, and the journey gain's confidence interval is above the owner's target. Otherwise the answer is "no measurable gain."