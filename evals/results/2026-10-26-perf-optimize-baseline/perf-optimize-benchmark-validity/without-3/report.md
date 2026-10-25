I reviewed `fixture/measurements.json` and `fixture/README.md`, which are the only files in the directory. There is no application runtime, so all of this is based on the saved data. I changed nothing and ran no new measurements.

## Verdict: none of the proposed gains justify adoption

| Claim | What the data shows | Valid? |
|---|---|---|
| **skip, 100x** (1 ms vs 100 ms) | `completed: 0`, `checksum: 0` against an expected 42000. It finishes no work at all. | **Invalid.** It fails the correctness check, so it isn't a speedup. |
| **drop-errors, 10x** (10 ms vs 100 ms) | `completed: 100`, `errors: 900`, `checksum: 4200`. It does 10% of the work. Per finished invoice it costs 10/100 = 0.1 ms, the same as baseline's 100/1000 = 0.1 ms. | **Invalid.** The "gain" comes entirely from failing 90% of exports, and per-item cost doesn't change. |
| **release candidate vs debug-old, 5x** (100 ms vs 500 ms) | Compares a release build with a debug build. `debug-old` also has no `attempted` field and no `journey_ms`. | **Invalid.** This measures the build type, not the code change. Against the release baseline the ratio is 1.0x. |
| **candidate vs baseline** | Both release builds, both correct (checksum 42000, 0 errors). | **Valid comparison, but it shows no gain** (details below). |

## Candidate vs baseline: the only fair comparison

| Metric | Baseline (n=3) | Candidate (n=3) | Difference |
|---|---|---|---|
| Component `ms` | mean 100, SD 10, range 90–110 | mean 100, SD 15, range 85–115 | **0 ms (0%)** |
| User journey `journey_ms` | mean 300, SD 10, range 290–310 | mean 300, SD ≈18, range 285–320 | **0 ms (0%)** |

**How uncertain this is** (Welch t-test, 3 runs per arm):
- Component: the 95% CI for the difference is about **±31 ms**, roughly ±30% of baseline.
- Journey: the 95% CI is about **±37 ms**, roughly ±12% of baseline.
- The best estimate is no change. The data can't rule out a regression or a gain of up to about 30%.
- The candidate is also more variable: its spread is about 1.5x baseline on `ms` and 1.8x on journey. That leans slightly against it if tail latency matters.
- The component accounts for only about a third of the journey (100 of 300 ms). Even a real 20% component gain would move the journey by only about 7%.

**Other problems that weaken any conclusion:**
1. **Batch ordering.** All baseline runs came first, then all candidate runs. Any drift over time (thermal, background load, disk cache) gets attributed to the variant.
2. **Missing fields.** The candidate has no `attempted` field, so "completed 1000 of 1000" isn't actually recorded. It's implied only by the checksum.
3. **Undocumented builds.** Compiler flags beyond the "release" label are missing, so the two release builds may not be equivalent.
4. **No profile, and the candidate's limiter is unknown.** Nothing says why the candidate should be faster.
5. **No journey data for skip or drop-errors.** Their claims can't be checked against what the user actually experiences.

**Decision:** don't adopt the candidate on performance grounds, because no improvement has been shown. If it has other merits (simpler code, a bug fix), it could be adopted as performance-neutral within the ±12% journey uncertainty, ideally after the check below confirms there's no regression.

## Next measurement plan (bounded)

**Correctness gate, applied to every run before its timing counts:** `attempted == completed == 1000`, `errors == 0`, `checksum == 42000`. Any run that fails is reported separately and excluded from timing.

**Setup:**
- Same host, same input, cold cache with the cache reset method written down, concurrency 1.
- Record the full compiler and linker flags, the toolchain version, and a commit hash for both builds.
- Both builds must be release, with identical flags apart from the code change.

**Design:**
- Interleave the two variants in randomized or ABBA order. Never run one whole batch and then the other.
- Analyse the runs as pairs, so drift cancels out.

**Primary metric:** `journey_ms` (open to downloaded file). `ms` is secondary.

**Sample size and stopping rule:**
- **Stage 1:** 30 interleaved pairs. Compute the paired mean difference and its 95% CI for both journey and `ms`.
  - If the journey CI lies entirely below −3% (−9 ms), adopt the candidate as a gain.
  - If the CI lies entirely within ±3%, it's neutral. Adopt only for non-performance reasons.
  - If the CI lies entirely above +3%, reject it as a regression.
- **Stage 2, only if Stage 1 is inconclusive:** add 60 more pairs, for a hard cap of 90. A minimum effect of about 5 ms at SD about 12 ms needs roughly 90 per arm at 80% power. Whatever the CI shows at 90 pairs is the final answer. Don't add runs past that.

**Diagnostics, one run each and not part of the timing statistics:**
- Profile baseline and candidate to find what limits each one (CPU, I/O, or locks). If the candidate's change doesn't touch the hot path, a component gain is unlikely to show up in the journey.

**Report:** for each variant, the median, p90 and max as well as the mean, the paired CI, and the excluded runs with their reasons. Report only measured values.