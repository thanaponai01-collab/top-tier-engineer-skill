I reviewed `fixture/measurements.json` and the README. There's no application runtime here, so everything below comes from the saved data. I ran nothing new and made up no numbers.

## Verdict: none of the proposed gains justify adoption

| Proposal | Claimed | Verdict | Why |
|---|---|---|---|
| **skip** | 100x | **Invalid** | `completed: 0`, `checksum: 0` (expected 42000). It doesn't do the work. It's 1 ms because nothing is exported. |
| **drop-errors** | 10x | **Invalid** | Only 100 of 1000 completed, with 900 errors, and the checksum is 4200, not 42000. That's a regression shown as a speedup. Its `errors` count also contradicts the "0 errors" style of the other runs, so it's a correctness failure, not a performance result. |
| **candidate vs debug-old** | 5x | **Invalid comparison** | It compares a release build with a debug build, so the 5x mostly measures compiler optimisation, not the change. `debug-old` also has no `attempted` field and no `journey_ms`. |
| **candidate vs baseline** | (implied gain) | **No gain shown** | This is the only like-for-like pair: both release builds, both 1000/1000 completed, both checksum 42000. The data shows no difference (see below). |

## Candidate vs baseline: the numbers

From the saved data (n=3 per arm, sample SD):

| Metric | Baseline mean ± SD | Candidate mean ± SD | Difference | Approx. 95% CI of difference (Welch, df≈3–4) |
|---|---|---|---|---|
| Export `ms` | 100 ± 10 | 100 ± 15 | **0 ms** | roughly ±31 ms (±31%) |
| Journey `journey_ms` | 300 ± 10 | 300 ± 18 | **0 ms** | roughly ±36 ms (±12%) |

- The point estimate is exactly zero on both metrics.
- The candidate's spread is wider (85–115 and 285–320), so it may be less consistent, though n=3 can't confirm that.
- With these intervals, a 25% gain or a 25% regression in export time would both fit the data. These measurements can't tell the two apart.

## Other problems with the measurements

1. **Batch order is confounded.** All baseline runs came first, then all candidate runs. Thermal state, background load, disk/page cache and time drift all line up with the variant.
2. **"Cold cache" isn't defined.** We don't know how it was enforced between runs, and with sequential batches cache state may not have been comparable.
3. **Fields are missing.** `candidate` and `debug-old` have no `attempted`, so "1000 of 1000" can't be fully checked. `skip` and `drop-errors` have no `journey_ms`.
4. **Build is only partly specified.** "Compiler flags beyond build label missing", so even release vs release isn't proven identical apart from the change.
5. **No profile, and the candidate's limiter is unknown.** We can't explain why the candidate would be faster, so we can't predict when it would help.
6. **n=3 per arm** is too small for differences under about 30% on export.
7. **Unit of benefit.** The user journey (open to downloaded file) is about 300 ms, and export is about 100 ms of it. Even a real 10% export gain would be about 3% of the journey, which is under this data's noise floor.

## Next measurement plan (bounded)

This is for candidate vs baseline only. Retire skip, drop-errors and debug-old as performance comparisons.

**Setup (fixed before any runs)**
- Both arms built from the same commit base with identical, recorded compiler flags, the same machine, and the same input set. Record the toolchain version and hashes of both binaries.
- Define cold cache explicitly (for example, process restart plus file-cache flush before each run) and apply it identically to both arms. Optionally run a separate warm-cache series.
- Concurrency 1, and log background load.

**Correctness gate (each run, before timing counts)**
- Record `attempted`, `completed`, `errors` and `checksum` for every run.
- Discard and flag any run that isn't 1000/1000 with 0 errors and checksum 42000. Any failure in the candidate blocks adoption.

**Design**
- Interleaved, randomised pairs (ABBA or a randomised order within each pair), not batches.
- **Journey (primary metric):** 40 pairs. With the observed SD (about 14 ms), that detects roughly a 3% (9 ms) difference at 80% power, α=0.05.
- **Export `ms` (secondary):** 100 pairs. With an SD of about 12 ms, that detects roughly a 5% difference.
- Hard cap: 2 rounds. If round 1 is inconclusive, run one more round of the same size and then stop. Don't keep adding runs until something comes out significant.
- One profiled run per arm (CPU, I/O, allocation) to find the candidate's limiter.

**Decision rule (fixed before any runs)**
- **Adopt** only if correctness passes in every run, the journey median improves by at least 3% with the 95% CI excluding 0, and p95 doesn't regress by more than 2%.
- **Reject** if correctness fails anywhere, or if the CI excludes a gain of 3% or more.
- **Otherwise** treat it as "no meaningful difference" and decide on non-performance grounds (complexity, risk).

**Report:** per-run raw values, median, p95, the CI of the paired difference, discarded runs with reasons, flags and hashes, and the profile summary.