I checked the numbers by hand from `fixture/measurements.json` and `fixture/README.md`. I made no changes to any files, and the application isn't included, so nothing new was measured.

## Decision: none of the four proposed gains justifies adoption

| Proposal | Claimed | Verdict | Why |
|---|---|---|---|
| **skip** | 100x | **Invalid** | `completed: 0` and `checksum: 0` against an expected 42000. It does no work, so the 1 ms is the cost of skipping the export. |
| **drop-errors** | 10x | **Invalid** | `completed: 100`, `errors: 900`, `checksum: 4200`. 90% of the work fails. It's fast because it does a tenth of the job, then reports `errors` as if that were acceptable. |
| **release candidate vs debug-old** | 5x | **Invalid comparison** | It compares a debug build with a release build, so most of the gap is probably build mode, not code. It also has no `attempted` field and no `journey_ms`. The compiler flags beyond the build label aren't recorded. |
| **candidate vs baseline** | (implied gain) | **No gain shown** | This is the only valid pairing: same build type, correct checksum, all 1000 completed. The means are identical (details below). |

## Candidate vs baseline: what the data supports

| Metric | Baseline (n=3) | Candidate (n=3) | Difference | Rough 95% CI (Welch, df ≈ 3) |
|---|---|---|---|---|
| `ms` | mean 100, SD 10 | mean 100, SD 15 | 0 | about ±31 ms (±31%) |
| `journey_ms` | mean 300, SD 10 | mean 300, SD 18 | 0 | about ±37 ms (±12%) |

- **Point estimate:** zero improvement on both the component time and the user journey.
- **Uncertainty:** with three runs per side, the data can't rule out the candidate being up to about 30% slower or faster on `ms`, or about 12% either way on the journey. The ranges overlap completely: 85–115 vs 90–110, and 285–320 vs 290–310.
- **Variance:** the candidate's spread is larger (journey 35 ms range vs 20 ms). That could be a tail-latency regression, or just noise at n=3.
- **Effect on the journey:** `ms` is about 100 of the 300 ms journey. Even removing it entirely would only make the journey about 1.5x faster. The rest of the journey isn't measured or explained.

## Confounds and gaps in the recorded conditions

1. **Batched order** ("baseline batch then candidate batch"): any drift over time, such as heat, background load or caches warming, falls entirely on one variant.
2. **"Cold cache" isn't defined:** there's no record of how it was reset before each run.
3. **Missing `attempted` field** on candidate and debug-old, so the completion rate can't be checked independently. The checksum matches, which helps, but it isn't proof.
4. **Compiler flags aren't recorded** beyond the release/debug label, so two "release" builds may not be equivalent.
5. **"Candidate limiter unknown":** the candidate may be throttled or rate-limited differently, which could hide or create differences.
6. **No profile**, so there's no explanation of what the candidate changed or where time goes in the journey.
7. **n=3 per variant**, with no warm-up policy, machine details or dates recorded.

## Next measurement plan (bounded)

**Scope:** baseline vs candidate only. Both must be release builds with the same recorded compiler flags and commit hashes. Skip, drop-errors and debug-old are excluded.

**Rule for counting a run as valid (set before measuring):** a run counts only if `attempted == completed == 1000`, `errors == 0` and `checksum == 42000`. Any failure is reported separately and never averaged in.

**Before running anything, set:**
- Main metric: `journey_ms` median. Secondary: `ms` median and p90.
- Adoption bar: journey median at least 5% (about 15 ms) faster, with the 95% CI of the difference entirely below 0, and p90 no worse by more than 5%.
- No-regression bar, if the candidate is wanted for other reasons: the upper end of the CI is under +5%.

**Procedure:**
1. Write down the cold-cache reset steps, the limiter settings for both variants, the machine, the OS, and power/thermal state.
2. Run in interleaved, randomised pairs (ABBA blocks) at concurrency 1, discarding one warm-up pair.
3. **Sample size:** with a journey SD of about 15 ms, detecting a 15 ms difference at 80% power needs about 16 pairs. Plan for **20 pairs**, which is 40 runs in total.
4. **Hard limit:** 30 pairs or one session, whichever comes first. If the CI still crosses the threshold at that point, stop and report the result as "inconclusive at ±X ms" rather than extending the test.
5. Take one profile per variant (one run each, not included in the timings) to find where the journey's roughly 200 ms outside `ms` is spent.

**Report:** per-run raw rows including all the integrity fields, medians, p90, the CI of the paired difference, and the number of excluded runs with the reason for each.

**Bottom line:** the only valid comparison shows a 0% change, with roughly ±12% uncertainty on the user journey. Don't adopt anything on this data. Run the 20–30 pair interleaved test above before deciding on the candidate.