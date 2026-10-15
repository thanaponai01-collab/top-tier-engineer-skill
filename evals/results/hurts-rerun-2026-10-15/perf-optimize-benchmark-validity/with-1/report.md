# Performance review: proposed gains in `fixture/measurements.json`

I followed perf-optimize in Measure mode and applied its benchmark-validity gate. No application runtime was supplied, so this review only analyses the saved data. Nothing was re-run, changed or invented.

**Verdict: none of the four proposed gains should be adopted.** Three come from invalid comparisons. The fourth (candidate vs baseline) is correct but inconclusive: its medians are identical.

## Before / after

| Metric | Baseline (release) | Candidate (release) | Change |
|---|---|---|---|
| Export median (min–max), n=3 | 100 ms (90–110) | 100 ms (85–115) | **0%** |
| Journey median (min–max), n=3 | 300 ms (290–310) | 295 ms (285–320) | −5 ms (−1.7%), well inside the noise |

The candidate didn't move the median. It made the export spread wider (30 ms vs 20 ms) and the slowest journey slower (320 vs 310 ms).

**Budget:** the owner gave no target. As an *assumption*, I'd propose: journey p50 ≥10% faster than baseline (≤270 ms) with no p95 regression and the checksum kept at 42000. The owner should confirm or replace it before any decision.

## Validity table

| Claim | Workload / config | Attempted / completed / errors / output check | Samples / order | Micro median (spread) | Journey median (spread) | Limiter | Decision |
|---|---|---|---|---|---|---|---|
| **skip "100×"** | release, same input | 1000 / **0** / 0 / checksum **0 ≠ 42000** | 3, batched | 1 ms (1–1) | not measured | n/a | **Rejected.** No work was done and the output is wrong. 1 ms is the cost of doing nothing. |
| **drop-errors "10×"** | release | 1000 / **100** / **900** / checksum **4200 ≠ 42000** | 3, batched | 10 ms (9–11) | not measured | unknown | **Rejected.** 90% of requests failed and the output is wrong. Per successful invoice it is 0.10 ms vs baseline's 0.10 ms, so there is no gain even on that basis. |
| **release candidate vs debug-old "5×"** | debug vs release | old run has no attempted count / 1000 / 0 / 42000 ✓ | 3, batched | 500 vs 100 ms | debug run has none | unknown | **Rejected.** This compares build modes, not code. The release *baseline* is already 100 ms, so the whole 5× comes from the build mode, and the code contributes nothing. |
| **candidate vs baseline** | both release; compiler flags beyond the build label missing | baseline 1000/1000/0/✓; candidate **attempted missing**/1000/0/✓ | 3 each, **baseline batch then candidate batch** (not interleaved) | 100 vs 100 ms | 300 vs 295 ms | **unknown, no profile** | **Inconclusive.** Output is correct, but the difference is within run-to-run spread. Order is confounded with drift, and 3 samples can't support any tail (p95) claim. |

## Uncertainty

- **Sample size:** with n=3 per arm, the "p95" is just the maximum value. The ranges overlap almost completely (export 85–115 vs 90–110; journey 285–320 vs 290–310).
- **Order confound:** each variant ran as a single batch. Drift such as thermals, background load or cache state can't be separated from the effect of the change.
- **Missing fields:** the candidate run has no `attempted` count, so dropped requests can't be ruled out. Compiler flags, hardware and dependency versions aren't recorded. There is no profile, and the limiter is unknown for every variant.
- **Cold cache only:** nothing is known about warm-cache behaviour.

## Bounded next measurement plan

This is a proposal only; none of it has run.

1. **Pin the workload and configuration.** Use the same 1000-invoice input and expected checksum 42000. Record the release build for both arms with identical flags, plus hardware, dependency versions, cold-cache procedure and concurrency 1. Fill in `attempted` for every run.
2. **Gate correctness on every sample.** Each sample must show completed = attempted = 1000, errors = 0 and checksum = 42000. Report failures; don't filter them out.
3. **Interleave.** Run paired ABBA blocks (baseline, candidate, candidate, baseline) with the same cache reset before each run, and keep the run order in the output. Measure both the export ms and the open-to-downloaded-file journey.
4. **Size the sample from variability, with a cap.**
   - Pilot with 10 ABBA blocks (20 runs per arm, about 40 cold journeys ≈ a few minutes plus reset time).
   - From the pilot, compute the spread of the paired journey differences and how many pairs it would take to resolve the 10% (≈30 ms) assumed target.
   - Hard cap of 30 blocks, or one hour of wall-clock time.
   - If the result still straddles zero at the cap, report it as inconclusive and stop. Don't keep adding runs until it turns green.
5. **Profile separately.** Do one profiled run per arm, kept apart from the timed runs, to name the limiter (CPU, I/O, serialization or something else). That decides whether the candidate even targets the cost in the journey: export is about 100 of the 300 ms, so even a perfect export change can't remove the other ~200 ms.
6. **Decision rule:**
   - **Adopt** only if correctness holds on every run and the median paired journey improvement meets the owner-confirmed target with its spread clear of zero. Then add a regression guard: a test that fails if the export journey p50 regresses.
   - **Reject** if the result is slower or any run is incorrect.
   - Otherwise it stays **inconclusive**.

Skip and drop-errors should not be re-measured as speedups. If dropping work is an intended product change, that's a separate correctness and product decision, not a performance gain.