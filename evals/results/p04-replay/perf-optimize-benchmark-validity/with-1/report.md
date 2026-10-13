I reviewed the saved file `fixture/measurements.json` against the perf-optimize benchmark checklist. There is no application to run, so every number below is worked out from the saved data, and the next-step plan is a proposal I have not run.

## Verdict: none of the four proposed gains justifies adoption

| Proposal | Claimed | Real useful work and output check | Verdict |
|---|---|---|---|
| **skip** | 100x | 0 of 1000 invoices exported, checksum 0 (expected 42000) | **Rejected.** It is fast because it does nothing. |
| **drop-errors** | 10x | 100 of 1000 exported, 900 errors, checksum 4200 | **Rejected.** 90% of the export fails. Per successful invoice it costs 10 ms ÷ 100 = 0.1 ms, the same as baseline's 100 ms ÷ 1000. No real speedup. |
| **release candidate vs debug-old** | 5x | Both give the correct checksum, but one is a debug build and the other a release build | **Rejected as a comparison.** The 5x comes from the build type, not the code. The fair comparison is against the release baseline, which is the next row. |
| **candidate vs baseline** (both release) | — | 1000 exported, 0 errors, checksum 42000 in both. Candidate is missing the `attempted` count. | **Inconclusive.** No measurable difference (see below). |

## Candidate vs baseline: the only valid comparison

| | Export time per run, median (range, std dev) | Full journey: open to downloaded file, median (range, std dev) |
|---|---|---|
| baseline | 100 ms (90–110, SD 10) | 300 ms (290–310, SD 10) |
| candidate | 100 ms (85–115, SD 15) | 295 ms (285–320, SD 18) |

- **Export time:** the medians are identical and the means are both 100 ms. There is no gain, and the candidate is less consistent.
- **Journey:** the median is 5 ms (1.7%) lower, but the mean is 300 ms in both. The two ranges overlap completely and the spread is larger than the difference.

Other problems with this data:
- **Only 3 runs each.** The spread estimates themselves are unreliable, and nothing can be said about worst-case (tail) times.
- **Runs weren't alternated.** All baseline runs came first, then all candidate runs, so any drift over time looks like a difference between them.
- **Missing records.** Compiler flags beyond "release"/"debug" weren't recorded. Candidate and debug-old have no `attempted` count. There is no profile, and nothing shows what limits the candidate's speed (CPU, disk, network, etc.).
- **No target.** The owner never said how much faster counts as worth adopting, so nothing can be judged against a goal.

## Next measurement plan (capped)

1. **Get a target first.** Ask the owner for the smallest journey gain that would justify adopting the candidate. If none is given, I'd assume 15 ms (5% of 300 ms) and label it as assumed.
2. **Same setup for both.** Use the same release artifact with compiler flags, hardware, dependency versions, cold-cache reset method and concurrency 1 written down.
3. **Record every run in full:** attempted, completed, errors, and checksum checked against 42000. Any run that fails the checksum counts as a failure and is reported, not filtered out.
4. **Pilot: 20 alternating pairs** (baseline, candidate, baseline, …, run in randomised order), measuring both export time and full journey time. This re-estimates the spread.
5. **Size the full run from the pilot.** Rough runs per variant ≈ 16σ²/d², where σ is the spread and d is the target gain.
   - With today's spread (about 15 ms): a 15 ms target needs about 16 runs; a 5 ms target needs about 150.
   - Cap: 150 pairs or 30 minutes of wall time, whichever comes first. Each journey takes about 0.3 s, so the cost is mostly in the cache resets.
   - Fix the stopping rule before starting.
6. **Decide once.** Compare the median journey difference against the run-to-run spread. If the result is within noise or below the target, the candidate is not adopted. Do not re-run until it comes out green.
7. **Profile separately**, in its own runs and not in the timed ones. This names what limits the candidate's speed so any future change targets a real cost.

Nothing in the application was changed and no new measurements were made.