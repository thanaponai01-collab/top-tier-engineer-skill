I followed the perf-optimize skill. The folder has only `fixture/measurements.json` and a README, with no application to run. So the skill's measuring tool wasn't used, and I judged the saved numbers against its benchmark-validity rules. **Nothing was run or re-measured; every number below comes from the file.**

## Decision: adopt none of the four proposed gains

| Proposal | Work done / output check | Timing (median, spread) | Verdict |
|---|---|---|---|
| **skip** ("100×") | 1000 attempted, **0 completed**, checksum **0** (expected 42000) | 1 ms, no user-journey timing | **Rejected.** It is fast because it does no work. |
| **drop-errors** ("10×") | 1000 attempted, **100 completed, 900 errors**, checksum **4200** | 10 ms (9–11), no journey timing | **Rejected.** The output is wrong and mostly errors. Per successful invoice it takes 10 ms / 100 = **0.1 ms**, exactly the same as baseline (100 ms / 1000). Even per unit there is no gain; it just does 10% of the work. |
| **candidate vs debug-old** ("5×") | debug-old: 1000 completed, checksum OK, **attempted not recorded** | 500 ms (490–510) vs 100 ms | **Invalid comparison.** It compares a debug build to a release build, so the 5× mostly measures build mode, not a code change. It can't be fixed by applying a multiplier. |
| **candidate vs baseline** | Both 1000 completed, 0 errors, checksum 42000. Candidate's **attempted is not recorded** | Function timing: **100 vs 100 ms**. Baseline spread 90–110, candidate 85–115. User journey: **295 vs 300 ms**. Baseline 290–310, candidate 285–320 | **Inconclusive.** See below. |

### Why candidate vs baseline is inconclusive
- **No measured gain.** The function timing has the same median, and the candidate's spread is wider. The 5 ms (~1.7%) journey difference falls well inside both spreads, and the candidate's slowest journey run (320 ms) is worse than baseline's slowest (310 ms).
- **Run order is confounded.** All baseline runs came first, then all candidate runs. Any drift over that time (thermal throttling, background load, cache state) can't be separated from the code change.
- **Configuration is incomplete.** Compiler flags beyond the "release" label, hardware and dependency versions are missing, so even release vs release isn't confirmed to be the same configuration.
- **Not enough samples.** Three runs per side shows nothing reliable about the slow tail (p95/p99), and the spread is ±10–15% of the median.
- **Limiter unknown.** There's no profile, and the file says "candidate limiter unknown", so nothing ties the candidate to a measured bottleneck (CPU, I/O, lock and so on).
- **No adoption target.** The data doesn't say what gain the owner would accept. I haven't invented one; someone needs to state it.

## Next measurement plan (bounded)
I haven't run any of this; it's a proposal.

1. **Pin the setup.** Same input and expected checksum 42000. Build baseline and candidate as release with **identical recorded compiler flags**, on the same machine, with the same dependency versions. Keep cold cache and concurrency 1, as in the file, and write down how the cache is reset between runs.
2. **Record work for every run.** Attempted, completed, errors and checksum. Any run that doesn't show 1000/1000/0/42000 makes that variant invalid; don't filter it out.
3. **Alternate the runs.** Use an ABBA order (baseline, candidate, candidate, baseline, and so on), each with a cold-cache reset. Record both function time and user-journey time, plus the order, all samples, the median and the spread.
4. **Size the run from the observed spread.** With a ±10–15 ms spread and a gain of 0–5 ms, separating them takes far more than 3 runs. Start with **20 alternated pairs**. Each pair costs about 0.8 s of journey time plus cache resets, so the cache resets set the cost. Stop at a budget the owner sets, for example 30 minutes or 100 pairs, whichever comes first.
5. **Profile separately.** Do one profiled run of each variant, outside the timed runs, to find the limiter. If the candidate's change doesn't touch where the profile shows time going, a gain is unlikely.
6. **Decide once, then stop.** Adopt only if the candidate is correct on every run, its journey gain stays outside the alternating-run spread, and it meets the owner's stated target. Otherwise report it as "no measurable gain" and don't keep rerunning until it passes. skip and drop-errors stay rejected unless they reach 1000/1000 with checksum 42000. If they do, they become ordinary candidates and go through steps 1–6.