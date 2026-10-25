# Review of the proposed performance gains in `fixture/measurements.json`

**None of the four proposed gains justifies adoption.** Two fail because the work isn't done (skip, drop-errors). One is invalid because it compares a debug build with a release build (debug-old). The only valid comparison, candidate vs baseline, is inconclusive: the median is unchanged and the 5 ms difference in the user journey is within the noise.

I only analysed the saved data. No application runtime was supplied, so I ran nothing, and the plan below hasn't been run either.

## Workload and decision
- **Workload:** export 1000 invoices; correct output has checksum 42000. The user journey runs from opening to having the downloaded file.
- **Conditions:** same input, cold cache, one run at a time.
- **Missing:**
  - compiler flags beyond the debug/release label
  - hardware and dependency versions
  - a profile
  - what limits the candidate (CPU, I/O, etc.)
  - a target from the owner. None is given, so I haven't invented an adoption threshold.

## Verdict per variant

| Variant | Attempted / completed / errors / checksum | Samples / order | Export time, median (range) | Journey time, median (range) | Limiter | Verdict |
|---|---|---|---|---|---|---|
| baseline | 1000 / 1000 / 0 / 42000 ✓ | 3, run as one batch first | 100 ms (90–110) | 300 ms (290–310) | unknown | Valid reference |
| skip ("100x") | 1000 / **0** / 0 / **0** ✗ | 3 | 1 ms | not measured | n/a | **Rejected:** no invoices exported, so it's fast because it does nothing |
| drop-errors ("10x") | 1000 / **100** / **900** / **4200** ✗ | 3 | 10 ms | not measured | n/a | **Rejected:** 90% of the work fails and the output is wrong. Per completed invoice it is 0.10 ms vs 0.10 ms, so no gain even then. |
| debug-old ("5x", the base for the 5x claim) | **attempted missing** / 1000 / 0 / 42000 | 3 | 500 ms (490–510) | not measured | unknown | **Invalid comparison:** debug vs release measures the build mode, not the code. Scaling it by a guessed multiplier wouldn't fix that. |
| candidate | **attempted missing** / 1000 / 0 / 42000 ✓ | 3, run as one batch after baseline | 100 ms (85–115) | 295 ms (285–320) | **unknown** | **Inconclusive:** see below |

### Why candidate vs baseline is inconclusive
- **No gain in export time.** Both medians are 100 ms, and the candidate's spread is wider (30 ms vs 20 ms).
- **Journey gain is noise.** It is −5 ms (−1.7%), against a run-to-run range of 20–35 ms. Three samples per side can't separate the two.
- **Order is confounded.** All baseline runs came first, then all candidate runs. Any drift over that time (thermal, background load, cache) would look like a difference between the variants.
- **Attempted count missing.** The candidate's completed count and checksum match, but without the attempted count the work counts can't be fully confirmed.
- **Compiler flags and limiter unknown.** I can't confirm the two release builds were built the same way, or say what the candidate changes.
- **No tail figures.** With 3 samples, any p95 claim would be made up.

## Next measurement plan (bounded)
Only candidate vs baseline is worth measuring again. Skip and drop-errors stay rejected: re-timing them can't fix wrong output. Debug-old should be dropped, or rebuilt as release with the same flags as the others before it's compared.

1. **Pin the setup and record it:** both release builds with identical, recorded compiler flags, the artifact hashes, hardware and dependency versions. Use the same 1000-invoice input and keep cold cache with an explicit, recorded cache reset before every run. One run at a time.
2. **Record correctness on every run:** attempted, completed, errors and a checksum check (42000). Any run that fails is reported as a failure, not filtered out.
3. **Alternate the variants:** pair runs in A-B / B-A order so the order is balanced, and keep the run order in the data. Record export time and journey time for every run.
4. **Size the sample from the noise, within a fixed budget:**
   - Start with about 10 pairs and measure how much the paired candidate−baseline difference varies.
   - Use that to work out how many pairs are needed to detect the owner's target.
   - Cap it at about 30 pairs or about 15 minutes, whichever comes first. The cold-cache reset, not the 0.1–0.3 s runs, will take most of the time.
   - If the cap is reached and the result is still within the noise, report it as inconclusive. Don't keep adding runs until it turns green.
5. **Get a target from the owner before deciding**, e.g. "journey p50 must drop by at least X ms". Adopt only if the paired difference in journey time clears that target, with correctness intact on every run. A faster export time alone doesn't count as a gain for users.
6. **Profile separately** (not during the timed runs) to find what limits the export, so any next change is chosen from a profile line rather than a hunch.
7. **If the gain is adopted,** add a check that fails when the gain slips past the agreed threshold.

**Decision needed from you or the owner:** the adoption target for journey p50. Without it, the candidate can only end as "inconclusive" or "no measurable difference."