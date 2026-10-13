I reviewed `fixture/measurements.json` and `fixture/README.md`. There is no application runtime here, so everything below comes from the saved data. All figures are worked out from the values in the file; I didn't change anything.

## Verdict: none of the proposed gains justifies adoption

| Proposal | Claimed | Outcome check | Verdict |
|---|---|---|---|
| **skip** | 100× | `completed: 0`, `checksum: 0` (expected 42000) | **Invalid.** It does no work, so this is not a speedup. |
| **drop-errors** | 10× | `completed: 100`, `errors: 900`, `checksum: 4200` | **Invalid.** It fails 90% of the work. It's faster because it does a tenth of the job. |
| **release candidate vs debug-old** | 5× | Debug vs release build, and `attempted` is missing on debug-old | **Invalid comparison.** It measures the compiler build mode, not the code change. The 5× is just debug-old (~500 ms) against any release build (~100 ms). The unmodified baseline also gets "5×". |
| **candidate vs baseline** | none stated | Checksum 42000 ✓, 0 errors ✓, but `attempted` is missing | **The only valid comparison, and it shows no gain.** Details below. |

## Candidate vs baseline: the one fair comparison

Using a 95% t-interval with n=3 (df=2, t=4.303):

| Metric | Baseline mean ± CI | Candidate mean ± CI | Difference |
|---|---|---|---|
| `ms` (export step) | 100 ± 24.8 (sd 10) | 100 ± 37.3 (sd 15) | **0 ms** |
| `journey_ms` (open to downloaded file) | 300 ± 24.8 (sd 10) | 300 ± 44.8 (sd 18.0) | **0 ms** |

- **The means are identical.** The candidate has more spread (85–115 vs 90–110).
- **The measurement can't detect a real change.** With n=3, an effect of roughly ±30 ms (±10% of the journey) could hide inside the noise in either direction. "No gain shown" does not mean "no regression."
- **The export step is only about a third of the journey** (100 of 300 ms). Even if the export got 2× faster, the user would only see about a 17% improvement. The other ~200 ms isn't attributed to anything.

## Problems with the measurement setup (from `conditions`)

1. **The runs were grouped by variant, not alternated** ("baseline batch then candidate batch"). Any drift over time (heat, background load, cache state) shows up as a variant difference.
2. **Only 3 cold-cache runs per variant.** Cold starts vary a lot, and three runs can't estimate that variance.
3. **The candidate has no `attempted` count** (debug-old doesn't either). So "1000 of 1000 completed" can't be fully confirmed, though the matching checksum suggests it's correct.
4. **Compiler flags beyond the build label weren't recorded.** Even the two release builds might not be built the same way.
5. **No profile, and the candidate's bottleneck is unknown.** Nothing explains why the change should be faster, so there's no hypothesis to test.
6. **Journey timings are missing for skip, drop-errors and debug-old.** Even setting their invalidity aside, they can't be compared on what the user experiences.

## Next measurement plan (bounded)

**Goal:** a single yes/no on whether the candidate improves `journey_ms` by at least 5% (15 ms) without breaking correctness.

1. **Fix the setup first, before any timing run.**
   - Rebuild baseline and candidate from the same toolchain with identical, recorded flags.
   - Record `attempted` on every run.
   - Drop skip, drop-errors and debug-old from the comparison.
2. **Correctness check on every run:** `attempted == completed == 1000`, `errors == 0`, `checksum == 42000`. Any run that fails disqualifies that variant; it doesn't just get left out of the stats.
3. **Sample size: 30 runs per variant**, alternated A-B-B-A (or randomized order), same machine, concurrency 1.
   - This is enough to detect a 10 ms difference with 80% power, assuming sd of about 13 ms. The calculation is n ≈ 2·(1.96+0.84)²·13²/10² ≈ 25, rounded up to 30.
   - Keep cold- and warm-cache runs as separate, labelled groups, and say up front which one decides the outcome. Cold is the user journey, so use cold.
   - Time cost is about 60 journeys × ~0.3 s plus resets, which is a few minutes.
4. **Profile one run of each variant** (export step plus the rest of the journey) to find the candidate's bottleneck and where the other ~200 ms goes.
5. **Analysis:** report the median and p90 of `journey_ms` and `ms`, with a bootstrap 95% CI on the difference in medians (candidate minus baseline).
6. **Decision rule, fixed before running:**
   - **Adopt** only if all correctness checks pass and the whole CI for the `journey_ms` difference sits at or below −15 ms.
   - **Reject** if the CI includes 0, or if p90 regresses by more than 15 ms.
   - **Stop after one round.** If it's inconclusive, don't add more runs. Go back to the profile and make a specific change aimed at the bottleneck before measuring again.

**Bottom line:** the 100×, 10× and 5× claims come from doing less work or comparing different builds. The only fair comparison shows no measurable gain, and three runs per side can't rule out a gain or a regression of up to about 10%.