None of the proposed gains justify adoption. Three of them come from comparisons that aren't valid, and the fourth (candidate vs baseline) shows no measurable difference. I only reviewed `fixture/measurements.json` and `fixture/README.md`. There's no application runtime here, so I ran nothing and the figures below are calculated from the saved data only.

## Decision on each proposed gain

| Claim | Verdict | Reason |
|---|---|---|
| **skip, 100x** (1 ms vs 100 ms) | Reject: invalid | `completed: 0` and `checksum: 0` against the expected 42000. It did none of the work. It's fast because it skips the export. |
| **drop-errors, 10x** (10 ms vs 100 ms) | Reject: invalid | `completed: 100`, `errors: 900`, `checksum: 4200`. It finished 10% of the workload. The time per completed invoice is 0.10 ms, the same as baseline (100 ms / 1000). So there's no speedup even per item, only lost output. |
| **release candidate vs debug-old, 5x** (100 ms vs 500 ms) | Reject: invalid | This compares a debug build with a release build, so it changes two things at once. Release baseline vs debug-old already shows the same 5x, which means the gap is the build mode, not the code change. `debug-old` also has no `attempted` field and no journey timing. |
| **candidate vs baseline** | Don't adopt as a performance gain | This is the only valid comparison (same release build, full output, correct checksum), and it shows no gain. See below. |

## Candidate vs baseline: the numbers

| Metric | Baseline (n=3) | Candidate (n=3) | Difference | Approx. 95% CI (Welch) |
|---|---|---|---|---|
| Export ms | 90 / 100 / 110 → mean 100, sd 10 | 85 / 100 / 115 → mean 100, sd 15 | 0 ms | about ±31 ms (±31%) |
| Journey ms (open to file downloaded) | 290 / 300 / 310 → mean 300, sd 10 | 285 / 295 / 320 → mean 300, sd 18 | 0 ms | about ±37 ms (±12%) |

- Both means are the same. The candidate's spread is wider (sd 15 vs 10 for export, 18 vs 10 for journey), which could mean less consistent timing, but three runs can't show that.
- With n=3 the data can't confirm a 10% improvement and can't rule out a 10% regression either.
- The export step is only about a third of the 300 ms journey. Even a 2x faster export would save about 50 ms (around 17%) of what the user sees. The journey time should be the primary metric.

## Other problems with the data

1. **Batches weren't interleaved.** All baseline runs happened first, then all candidate runs, so any drift (thermal, background load, disk cache) gets counted as a code difference.
2. **Build flags are unknown** beyond the release/debug label, so even candidate vs baseline might not be like-for-like.
3. **No profile, and the candidate's bottleneck is unknown.** Nothing explains why the candidate would be faster, and the data shows it isn't.
4. **Completeness records are uneven.** `candidate` and `debug-old` have no `attempted` count. `skip`, `drop-errors` and `debug-old` have no journey timing.
5. **Cold cache only, and nothing about warm-up** (whether the first run was discarded). Three cold runs are dominated by noise.
6. **There's no pass/fail check.** Two variants that produced wrong output were still presented as speedups.

## Next measurement plan (capped)

**Scope:** baseline vs candidate only. Drop skip, drop-errors and debug-old; they can't be fixed by measuring them more.

1. **Validity check on every run.** `attempted == completed == 1000`, `errors == 0`, `checksum == 42000`. Any run that fails is recorded as a failure and never counted as a time.
2. **Same build.** Both variants as release builds, with the exact compiler and linker flags, commit hashes and toolchain versions recorded.
3. **Interleaved order.** Use ABBA blocks (or a randomized order) on the same machine with background load noted, so drift hits both variants equally.
4. **Primary metric:** journey ms (open to downloaded file). Export ms is secondary.
5. **Sample size: 25 runs per variant for each cache state** (cold, and warm with the first run discarded). That's 100 runs in total, and it stops there. The estimate assumes sd of about 12–15 ms, which comes from only three runs per variant, so check the sd after the first 10 per variant and stop early if it's much larger. At that sd, 25 runs can detect a 10 ms (10%) export change or a 15 ms (5%) journey change with about 80% power at α=0.05.
6. **Adoption rule, written down before running.** Adopt only if the 95% CI for the journey difference is entirely below −5% (or another threshold you choose before the runs), with zero validity failures and p95 not worse than baseline. If not, report "no detectable gain" and keep baseline.
7. **One profile of each variant** to find where the time goes in the candidate. If it's I/O or the download step, no export-code change will improve the journey.
8. **Report:** median, p95, mean ± CI, the run counts, and every failed run. No numbers carried over from the current data.

**Recommendation:** keep baseline. Run steps 1–8 before considering the candidate again. Drop the 100x, 10x and 5x claims.