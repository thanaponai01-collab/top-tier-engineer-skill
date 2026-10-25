I ran nothing. The fixture has only `measurements.json` and a README, and no application to run, so the skill's measure/change/guard helper doesn't apply. I judged the saved numbers against the skill's benchmark-validity rules. I changed no files and made up no measurements.

## Verdict: none of the four proposed gains justifies adoption

| Proposal | Workload / config | Attempted / completed / errors / checksum | Samples | Speed (median, range) | Journey (median, range) | Limiter | Decision |
|---|---|---|---|---|---|---|---|
| **skip** ("100x") | release | 1000 / **0** / 0 / **0** (expected 42000) | 3 | 1 ms (1–1) | not measured | unknown | **Rejected.** It did no work and the checksum is wrong. "1 ms for nothing" is not a speedup. |
| **drop-errors** ("10x") | release | 1000 / **100** / **900** / **4200** | 3 | 10 ms (9–11) | not measured | unknown | **Rejected.** 90% of the invoices errored and the checksum is wrong. Per completed invoice it costs 10 ms / 100 = **0.1 ms**, the same as baseline's 100 ms / 1000 = **0.1 ms**. So even its own numbers show no gain: it just did a tenth of the work. |
| **candidate vs debug-old** ("5x") | debug vs release | debug-old: *attempted missing* / 1000 / 0 / 42000 | 3 | 500 (490–510) vs 100 (85–115) | debug-old not measured | unknown | **Invalid comparison.** A debug build against a release build measures the build mode, not a code change. The fair comparison, candidate against the release baseline, is the next row and shows no gain. |
| **candidate vs baseline** | both release; other compiler flags not recorded | candidate: *attempted missing* / 1000 / 0 / 42000 ✓ | 3 each, all baseline runs then all candidate runs | **100 vs 100** (90–110 vs 85–115) | 300 vs 295 (290–310 vs 285–320) | unknown; no profile | **Inconclusive: no gain shown.** The median speed is the same. The journey's 5 ms (1.7%) difference is smaller than the 25–35 ms spread inside each variant. |

## Invalid comparisons and uncertainty

- **Wrong output counts as failure.** The skip and drop-errors timings only look fast because the useful work wasn't done. Correctness comes before speed.
- **Build mode confound.** Debug vs release can't show a code gain. You also can't convert between them with an assumed multiplier, so the 5x tells us nothing about the code.
- **Order confound.** The baseline batch ran first, then the candidate batch. Any drift over time, such as heat, background load or cache state, lines up exactly with the variant.
- **Configuration gaps.** Compiler flags beyond the "release" label, hardware and dependency versions weren't recorded. Neither the candidate nor debug-old recorded `attempted`, so we can't rule out that some invoices were dropped.
- **Too few samples.** Three runs per variant with about ±10–15% spread can't detect a difference below roughly 20%. Slowest-run figures (tail latency) can't be claimed at all.
- **The limiter is unknown and nothing was profiled.** It isn't known whether CPU, I/O or something else is the bottleneck, so there's no evidence that the candidate's change targets where the time goes.
- **No adoption threshold was given.** I haven't invented one. Whoever owns the decision needs to state what gain is worth adopting.

## Next measurement plan (bounded)

1. **Pin the setup.** Use the same release artifact recipe with full compiler flags recorded, and the same hardware, dependency versions and input. Keep cold cache and concurrency 1, and use the same cache-reset step before every run. Ask the owner to state the gain that matters, for example "at least 5% on the user journey".
2. **Record correctness on every run.** Log attempted, completed, errors and checksum for both variants. Throw out any run that isn't 1000 / 1000 / 0 / 42000, and report how many were thrown out.
3. **Alternate the runs.** Run in a balanced order (ABBA…), so neither variant always goes first, and time the export step and the full open-to-downloaded-file journey in the same run.
4. **Size the run from the observed spread.**
   - Start with 30 alternating pairs. At about 0.4 s per run plus the cache reset, that's a few minutes.
   - Compute the median of the paired differences with a bootstrap 95% confidence interval.
   - If the interval still crosses zero but could include the owner's threshold, extend to at most 100 pairs. About 100 per variant is what detecting a 5% change takes at the observed ~12 ms spread.
   - Stop there either way:
     - **Adopt** only if the whole interval is past the threshold on the journey, not only the export step.
     - **Reject** if the interval sits inside ±threshold.
     - Otherwise **report it as inconclusive.** Don't keep re-running until it comes out green.
5. **Profile separately, outside the timed runs,** to name the limiter and confirm the candidate's change hits something that takes a real share of the time.
6. **Re-measure debug-old only if the history matters,** and only as a release build. The 5x figure shouldn't be cited.

**Bottom line:** keep the baseline. Skip and drop-errors are broken, the 5x comes from build mode, and the candidate has shown no measurable gain so far. Steps 1–4 are what can still show whether it has one.