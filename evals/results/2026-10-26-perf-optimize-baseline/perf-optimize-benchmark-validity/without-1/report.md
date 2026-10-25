## Verdict: adopt none of them

None of the four proposals shows a gain that is both real and valid. Three compare against work that was never done or against a different build. The fourth, candidate vs baseline, shows no difference at all.

| Proposal | Claimed | Does the comparison hold? | Why |
|---|---|---|---|
| **skip** | 100x | **No.** | `completed: 0`, `checksum: 0` against an expected 42000. It ran 1 ms because it exported nothing. This is a correctness failure, not a speedup. |
| **drop-errors** | 10x | **No.** | 900 of 1000 failed and the checksum is 4200, i.e. 10% of the work. Per completed invoice it's about 0.1 ms, the same as baseline's 0.1 ms. Effective gain is about 1x, and it breaks 90% of exports. |
| **release candidate vs debug-old** | 5x | **No.** | A debug build compared with a release build measures the compiler settings, not the code change. `debug-old` also has no `attempted` field or journey data. Compared with the like-for-like release baseline, the candidate's gain is nothing. |
| **candidate vs baseline** | (implied) | **Valid pairing, but no gain shown.** | Details below. |

## Candidate vs baseline: the uncertainty

These come straight from the saved arrays (n = 3 each, sample SD):

| Metric | Baseline mean ± SD | Candidate mean ± SD | Difference |
|---|---|---|---|
| Component `ms` | 100 ± 10 | 100 ± 15 | **0** |
| User journey `journey_ms` | 300 ± 10 | 300 ± 18 | **0** |

- The means are identical on both metrics, so the t-statistic is 0. The candidate's spread is wider (85–115), which hints at a little more variance rather than a speedup.
- With n = 3 and SD around 15, the 95% interval on the difference is very wide: roughly ±25–30 ms on the component. A real gain or loss of about 25% could be hidden here.
- **Amdahl limit:** the component is about 100 of the 300 ms journey. Even an infinitely fast component would make the user journey at most about 33% faster. A 2x component speedup would give only about 17%.

## Other problems with the data
- **Batches weren't interleaved** ("baseline batch then candidate batch"). Drift from thermals, background load or cache state is mixed in with the variant.
- **"Cold cache"** isn't defined (OS page cache, app cache or both?), and with 3 runs the first-run effects aren't separated out.
- **Compiler flags beyond the build label weren't recorded**, so "release" vs "release" isn't proven to be the same build.
- **`attempted` is missing** for both `candidate` and `debug-old`, so completeness can't be fully checked. `completed`, `errors: 0` and the checksum do match.
- **No profile, and the candidate's limiter is unknown.** There's no explanation of what the change was meant to speed up.
- **Journey data is missing** for skip, drop-errors and debug-old.

## Next measurement plan (bounded)

1. **Correctness gate for every run:** `attempted == completed == 1000`, `errors == 0`, `checksum == 42000`. Any run that fails is thrown out and reported, never timed as a win.
2. **Like-for-like builds:** baseline and candidate both release, with the full compiler flags, commit hash and toolchain version recorded. Drop `debug-old` from the decision.
3. **Interleaved, randomized order** (ABBA or randomized blocks) on the same machine and input at concurrency 1. Record the host, background load and power mode.
4. **Sample size:** about 35 runs per arm. That detects a 10 ms (10%) component difference at 80% power and α = 0.05, given SD ≈ 15. Add 3 discarded warm-up runs if you report warm numbers, and define precisely how "cold" is produced if you report cold numbers. Report cold and warm separately.
5. **Primary metric is `journey_ms`; `ms` is secondary.** Report median, p95 and a bootstrap 95% CI on the difference.
6. **Decision rule, fixed before the run:** adopt only if the journey CI lies entirely below −3% (or whatever threshold you choose) and correctness holds on 100% of runs. If the CI includes 0, the result is "no demonstrated gain".
7. **One profile per arm** (CPU plus I/O wait) to find the candidate's limiter and confirm the change affects the part of the journey that dominates.
8. **Budget cap:** 70 measured runs plus warm-ups, one session. If the result is still inconclusive, stop and report the CI rather than adding runs until it looks significant.

I didn't modify anything or produce new measurements; everything above is calculated from `fixture/measurements.json`.