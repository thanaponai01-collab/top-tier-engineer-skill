I recommend adopting none of the four proposed gains. Two of them come from runs that didn't do the work, one compares a debug build against a release build, and the candidate shows no gain at all in the saved data.

There was no `measurements.json` at the top level; the data is in `fixture/measurements.json`, with a one-line `fixture/README.md` that lists the four claims. I only read these files: nothing was run or changed, and every number below is from that file or calculated from it.

## Workload and success criteria

The workload exports 1000 invoices. A run only counts if it completed all 1000 with 0 errors and produced checksum 42000. The file times both the export step (`ms`) and the full user journey from open to downloaded file (`journey_ms`).

| Variant | Completed / errors | Checksum | Export ms (mean) | Journey ms (mean) | Claimed |
|---|---|---|---|---|---|
| baseline (release) | 1000 / 0 | 42000 ✔ | 100 (90–110) | 300 (290–310) | — |
| skip | **0** / 0 | **0** ✘ | 1 | *missing* | 100x |
| drop-errors | **100 / 900** | **4200** ✘ | 10 | *missing* | 10x |
| debug-old (**debug**) | 1000 / 0 | 42000 ✔ | 500 | *missing* | 5x |
| candidate (release) | 1000 / 0 | 42000 ✔ | **100** (85–115) | **300** (285–320) | ? |

## Verdict on each claim

- **skip, 100x: invalid.** It completed 0 invoices and the checksum is 0. It is fast because it doesn't export anything.
- **drop-errors, 10x: invalid.** 90% of the invoices failed and the checksum is 4200, one tenth of what it should be. The speed comes from dropping 90% of the work, and failing silently is a correctness regression.
- **candidate vs debug-old, 5x: invalid comparison.** It compares a release build with a debug build. The 5x mostly measures the effect of the build settings, not the code change. The release baseline already runs at 100 ms, so the honest comparison is candidate vs baseline.
- **candidate vs baseline: no gain shown.** Both have a mean of exactly 100 ms for export and 300 ms for the journey. The candidate is also more variable (export spread ±15 ms vs ±10 ms; journey standard deviation about 18 ms vs 10 ms). The data supports neither adopting nor rejecting it.

## How uncertain the numbers are

- **Too few runs.** Each variant was timed only 3 times. For the candidate minus baseline difference, the 95% confidence interval is roughly 0 ± 30 ms on export (±30%) and 0 ± 37 ms on the journey (±12%). An effect smaller than about 12% on the journey could not be seen with this data.
- **Run order is a confound.** All baseline runs came first, then all candidate runs. Machine warm-up, thermal state or background load could easily account for 10% either way.
- **Only cold-cache runs at concurrency 1.** Steady-state and multi-user behaviour weren't measured.
- **Missing details:**
  - Compiler flags beyond the "release"/"debug" label weren't recorded.
  - No profile was taken, and the candidate's bottleneck is unknown.
  - debug-old and candidate have no `attempted` field, so completion can't be checked the same way for every variant.
- **Speeding up the export step barely moves what users see.** Export is about 100 of the 300 ms journey. Even an export that took zero time would only make the journey 1.5x faster, so speedups on the export step overstate the user-facing gain. Only skip and drop-errors were claimed on export time, and neither has journey timings.

## Next measurement plan (fixed size)

1. **Correctness gate first.** Each run must show attempted = completed = 1000, errors = 0 and checksum = 42000, recorded per run. Any run that fails is thrown out of the timing data, and that variant is disqualified.
2. **Same build for both.** Build baseline and candidate as release from the same toolchain, and save the full compiler and linker flags and the commit IDs with the results.
3. **Alternate the runs.** Run baseline and candidate in a random interleaved order (A B B A …) on the same machine and input, with a few untimed warm-up runs first.
4. **Fixed sample size.** 20 timed runs per variant, separately for cold cache and warm cache, at concurrency 1. That is 80 timed runs in total. Then a smaller follow-up at a realistic concurrency (for example 4) with 10 runs per variant. Decide these numbers in advance and don't stop early once a result looks good. With about 15 ms of journey variation, 20 runs per side detects a journey change of roughly 3%.
5. **Main measure: the user journey.** Report the median and the 95th percentile with a 95% confidence interval (bootstrap or Welch's t-test). Export time is a secondary measure.
6. **Rule to adopt, decided in advance.** Adopt the candidate only if the journey median improves by at least 5% (the team should set this number), the confidence interval excludes zero, the 95th percentile doesn't get worse, and the correctness gate passes on every run. If the change is smaller than about 3% either way, call it no difference.
7. **One profile per variant.** Capture this to find out what actually limits the candidate (CPU, I/O, network or locks), so the next change has a target.

If the team wants to revisit skip or drop-errors, they first have to pass the correctness gate. As they stand, they are not performance options.