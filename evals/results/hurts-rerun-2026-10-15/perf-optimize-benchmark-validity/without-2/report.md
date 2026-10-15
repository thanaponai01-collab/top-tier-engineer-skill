I reviewed `fixture/measurements.json` and `fixture/README.md`. No application code is included, so this is based only on the saved data. I didn't change anything or run anything new.

## Verdict: adopt none of the proposed gains

| Proposal | Claimed | Valid? | Why |
|---|---|---|---|
| `skip` | 100x | **Invalid** | `completed: 0`, `checksum: 0` against the expected 42000. It does no work, so it's 1 ms. |
| `drop-errors` | 10x | **Invalid** | 900 of 1000 failed, `completed: 100`, `checksum: 4200`. It's faster because it exports 10% of the invoices and drops the rest. |
| release candidate vs `debug-old` | 5x | **Invalid comparison** | It compares a debug build with a release build. Most of the 500→100 ms difference is just the build mode. It also has no `attempted` field and no `journey_ms`. |
| `candidate` vs `baseline` | — | **Valid comparison, but no gain** | See below. |

## Candidate vs baseline: the only valid comparison

Both are release builds, and both completed 1000/1000 with checksum 42000. One gap: the candidate run has **no `attempted` field**, so we can't confirm it attempted all 1000 invoices.

| Metric | Baseline (n=3) | Candidate (n=3) | Difference | Approx. 95% CI on difference |
|---|---|---|---|---|
| Export `ms` | mean 100, sd 10 (90–110) | mean 100, sd 15 (85–115) | **0 ms** | about ±30 ms (±30%) |
| Journey `journey_ms` | mean 300, sd 10 (290–310) | mean 300, sd 18 (285–320) | **0 ms** | about ±35 ms (±12%) |

(These are Welch intervals from n=3. With so few runs the intervals themselves are rough.)

The means are identical and the candidate varies more. The data can't separate "no effect" from an effect of up to about ±30% in export time, so it doesn't support adopting the candidate. It also doesn't rule out a small gain or a small regression.

## Other problems that weaken any conclusion
- **The runs were batched, not interleaved.** All baseline runs came before all candidate runs, so any change over time (heat, background load, disk cache) gets mixed in with the variant.
- **n=3 per variant.** That's too few runs to estimate spread or tail latency.
- **Compiler flags weren't recorded** beyond the release/debug label, so we can't confirm the two release builds were built the same way.
- **There's no profile, and the candidate's bottleneck is unknown.** We don't know what the candidate changed or where time is spent. Journey time (300 ms) is about 3× export time (100 ms), so about 200 ms is outside the export step, and a change only to export can improve the journey by at most about a third.
- **The runs are cold-cache only.** That's fine as a stated condition, but the results may not apply to warm-cache use.

## Next measurement plan (bounded)
Scope: baseline vs candidate only, both release builds with identical recorded flags, same input, cold cache, concurrency 1.

1. **Validity check on every run.** A run counts only if `attempted = completed = 1000`, `errors = 0` and `checksum = 42000`. Record every field for both variants, including `attempted`. Report invalid runs; don't silently drop them.
2. **Record the environment once.** Compiler and flags for both builds, machine, OS, power plan, and the cold-cache reset procedure.
3. **Interleave the runs.** Use a randomized or ABBA order with 2–3 discarded warm-up cycles. Measure export `ms` and `journey_ms` in the same runs.
4. **Fix the run count in advance.** Start with 30 pairs. Analyze the paired differences: median, a bootstrap 95% CI, and p95.
5. **Decide in advance what counts as a gain.** For example: adopt only if the journey CI lies entirely below −5% (a ≥15 ms improvement) and p95 does not get worse.
6. **Set a hard cap.** If the CI still crosses the threshold after 30 pairs, extend once to 100 pairs. Each run is under 0.5 s, so the cap is mostly cold-cache reset time. If it's still unresolved at 100 pairs, record "no meaningful difference" and stop.
7. **Profile one valid run of each variant** to find the candidate's bottleneck and to see where the roughly 200 ms of non-export journey time goes. That's likely the bigger opportunity.

Until that data exists: reject `skip` and `drop-errors` as incorrect, retire the debug-vs-release 5x claim, and keep the candidate unproven.