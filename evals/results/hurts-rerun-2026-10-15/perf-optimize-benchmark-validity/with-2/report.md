I followed the perf-optimize skill and its benchmark-validity reference. No runtime came with the files, so this review is based only on the saved data in `fixture/measurements.json`. I ran nothing, measured nothing and changed no application files.

## Verdict: adopt none of the proposed gains

Before → after on the only fair comparison (baseline vs candidate): the median export time is 100 ms → 100 ms, and the median user-facing time (open the export through to the downloaded file) is 300 ms → 295 ms. That journey difference is about 1.7%, well inside the noise. The candidate costs added complexity and buys no gain the data can show. Its result is **inconclusive**, and the other three claims are **invalid**.

| Proposal | Work done / errors / checksum | Samples | Export time, median (range) | Journey time, median (range) | Limiter | Verdict |
|---|---|---|---|---|---|---|
| baseline (release build) | 1000/1000, 0 errors, 42000 ✓ | 3, batched | 100 (90–110) | 300 (290–310) | unknown | reference |
| **skip "100×"** | **0 of 1000 completed**, checksum 0 ✗ | 3 | 1 | not measured | n/a | **Rejected.** It is fast because it does no work. |
| **drop-errors "10×"** | **100 of 1000 completed, 900 errors**, checksum 4200 ✗ | 3 | 10 (9–11) | not measured | n/a | **Rejected.** It produces wrong output with a 90% error rate. Even counted per successful invoice it takes 10 ms / 100 = 0.1 ms, the same as baseline (100 ms / 1000). There is no real gain. |
| **release candidate vs debug-old "5×"** | debug-old: 1000 completed, attempted count missing, 42000 ✓ | 3 | 500 vs 100 | not measured | n/a | **Rejected.** This compares a debug build with a release build, so the build mode explains the gap, not the code. The release baseline already runs at 100 ms, so the "5×" is debug overhead. |
| **candidate vs baseline** | 1000 completed, **attempted count missing**, 42000 ✓ | 3, batched after baseline | 100 (85–115) | 295 (285–320) | **unknown** | **Inconclusive.** See the uncertainty list below. |

## Uncertainty in the candidate vs baseline comparison

- **Order confound:** all baseline runs happened first, then all candidate runs. Any drift over time (heat, background load, caches) is mixed in with the effect of the change.
- **Too few samples:** three runs per side. The ranges overlap almost completely, and the candidate's spread is wider (30 ms vs 20 ms on export time, 35 ms vs 20 ms on journey time). Nothing can be said about p95 from three samples.
- **Configuration gaps:** compiler flags beyond the "release"/"debug" label weren't recorded. Neither were the artifact identity, hardware or dependency versions.
- **Missing work count:** the candidate run has no `attempted` field, so I can't confirm it ran the same 1000-invoice workload as baseline. Its checksum matches, which is reassuring but not a substitute.
- **No profile and no limiter:** nobody has shown what bounds the export (CPU, I/O, locks), so there is no hypothesis for why the candidate *should* be faster.
- **No target:** none was given. I'm assuming one: a journey p50 drop of at least 5% (≥15 ms) with no loss of correctness. The owner needs to confirm or replace that number.

## Next measurement plan (fixed budget, decision rules set before running)

1. **Pin the setup.** Build both variants as release with identical, recorded compiler flags. Record the artifact hashes, hardware, dependency versions, cold-cache procedure and concurrency 1. Use the same frozen set of 1000 invoices, with checksum 42000 as the correctness check.
2. **Correctness check on every run.** Record attempted, completed, errors and checksum. Any run that isn't 1000/1000/0/42000 marks that variant invalid; it does not get filtered out and quietly retried.
3. **Alternate the runs** (ABBA…) with the cache reset the same way before each run. Record export time and journey time, plus run order.
4. **Sample size from the observed noise.** The variation seen so far is roughly ±10 ms on a 300 ms journey. Detecting the assumed 15 ms difference needs only about 10 pairs; detecting the 5 ms difference seen so far would need about 60. I propose:
   - a fixed 20 pairs (40 runs, a few minutes plus cache-reset time) as stage 1;
   - a hard cap of 60 pairs if stage 1 is borderline.
   No further reruns beyond that.
5. **Profile separately**, in a run that isn't timed, to identify the limiter for both variants. Without that, a positive result still lacks an explanation.
6. **Decision rules:**
   - **Adopt** only if the candidate is fully correct, its journey median improves by at least the owner's target, and the difference falls outside the spread of the alternating samples. Then add a guard (a budget check on journey p50) so the gain can't quietly slip.
   - **Reject** if the difference is within the noise at the cap.
   - Do not report the export-time (micro) numbers as a user-facing gain.

**Dead ends to record so nobody repeats them:** skipping the work, dropping failing items, and comparing debug builds against release builds. None of these is a performance optimization.